"""Bootstrap ``config/auth_config.yaml`` with a single admin user.

Idempotent-ish: refuses to overwrite an existing file unless --force is given.
"""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

import bcrypt
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import AUTH_CONFIG_PATH, COOKIE_EXPIRY_DAYS, COOKIE_NAME


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--username", default="admin")
    ap.add_argument("--email", default="admin@company.com")
    ap.add_argument("--name", default="Administrator")
    ap.add_argument("--force", action="store_true", help="Overwrite existing config")
    args = ap.parse_args()

    if AUTH_CONFIG_PATH.exists() and not args.force:
        raise SystemExit(f"{AUTH_CONFIG_PATH} exists. Re-run with --force to overwrite.")

    pw = getpass.getpass(f"Password for {args.username}: ")
    if not pw:
        raise SystemExit("empty password")

    hashed = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

    config = {
        "credentials": {
            "usernames": {
                args.username: {
                    "email": args.email,
                    "name": args.name,
                    "password": hashed,
                    "roles": ["admin"],
                }
            }
        },
        "cookie": {
            "name": COOKIE_NAME,
            "key": "REPLACED_BY_ENV_COOKIE_KEY",
            "expiry_days": COOKIE_EXPIRY_DAYS,
        },
        "pre-authorized": {"emails": []},
    }

    AUTH_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUTH_CONFIG_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, allow_unicode=True)

    print(f"Wrote {AUTH_CONFIG_PATH}. Remember to set COOKIE_KEY in .env.")


if __name__ == "__main__":
    main()
