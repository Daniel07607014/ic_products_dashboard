"""User CRUD against the ``users`` table — the MySQL replacement for
``config/auth_config.yaml``.

No Streamlit imports here: the admin UI calls these, and so can scripts.
"""
from __future__ import annotations

import bcrypt
from sqlalchemy import text

from src.data.db import get_engine

USERS_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL DEFAULT '',
    password_hash VARCHAR(60) NOT NULL,
    role ENUM('admin','viewer') NOT NULL DEFAULT 'viewer',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
"""


def ensure_users_table() -> None:
    with get_engine().begin() as conn:
        conn.execute(text(USERS_DDL))


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def fetch_all_users() -> list[dict]:
    """All users (active or not), for the admin UI listing."""
    with get_engine().connect() as conn:
        rows = conn.execute(text(
            "SELECT username, name, email, role, is_active, created_at FROM users ORDER BY username"
        )).mappings().all()
    return [dict(r) for r in rows]


def fetch_active_credentials() -> dict:
    """Active users shaped as the streamlit-authenticator ``credentials`` dict."""
    with get_engine().connect() as conn:
        rows = conn.execute(text(
            "SELECT username, name, email, password_hash, role FROM users WHERE is_active = 1"
        )).mappings().all()
    return {
        "usernames": {
            r["username"]: {
                "name": r["name"],
                "email": r["email"],
                "password": r["password_hash"],
                "roles": [r["role"]],
            }
            for r in rows
        }
    }


def create_user(username: str, name: str, email: str, password: str, role: str = "viewer") -> None:
    if role not in ("admin", "viewer"):
        raise ValueError(f"unknown role: {role}")
    if not username or not password:
        raise ValueError("username and password are required")
    with get_engine().begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (username, name, email, password_hash, role) "
                "VALUES (:u, :n, :e, :p, :r)"
            ),
            {"u": username, "n": name or username, "e": email, "p": _hash(password), "r": role},
        )


def upsert_user_with_hash(username: str, name: str, email: str, password_hash: str, role: str) -> bool:
    """Insert a user whose bcrypt hash already exists (yaml migration).

    Returns True if inserted, False if the username was already present.
    """
    with get_engine().begin() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM users WHERE username = :u"), {"u": username}
        ).first()
        if exists:
            return False
        conn.execute(
            text(
                "INSERT INTO users (username, name, email, password_hash, role) "
                "VALUES (:u, :n, :e, :p, :r)"
            ),
            {"u": username, "n": name or username, "e": email or "", "p": password_hash, "r": role},
        )
        return True


def set_active(username: str, active: bool) -> None:
    with get_engine().begin() as conn:
        conn.execute(
            text("UPDATE users SET is_active = :a WHERE username = :u"),
            {"a": 1 if active else 0, "u": username},
        )


def reset_password(username: str, new_password: str) -> None:
    if not new_password:
        raise ValueError("password must not be empty")
    with get_engine().begin() as conn:
        conn.execute(
            text("UPDATE users SET password_hash = :p WHERE username = :u"),
            {"p": _hash(new_password), "u": username},
        )
