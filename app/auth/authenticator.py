"""streamlit-authenticator wrapper.

Every page that needs auth calls :func:`require_login` at the top.
Config is read once from ``config/auth_config.yaml`` and cached in session_state.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

from config.settings import AUTH_CONFIG_PATH, COOKIE_EXPIRY_DAYS, COOKIE_KEY, COOKIE_NAME


def _load_config(path: Path) -> dict:
    if not path.exists():
        st.error(
            f"Auth config not found at `{path}`. "
            "Copy `config/auth_config.yaml.example` and generate password hashes "
            "with `python deploy/scripts/hash_password.py`."
        )
        st.stop()
    with path.open("r", encoding="utf-8") as f:
        return yaml.load(f, Loader=SafeLoader)


def get_authenticator() -> stauth.Authenticate:
    if "authenticator" not in st.session_state:
        config = _load_config(AUTH_CONFIG_PATH)
        config.setdefault("cookie", {})
        config["cookie"]["name"] = config["cookie"].get("name", COOKIE_NAME)
        config["cookie"]["key"] = COOKIE_KEY
        config["cookie"]["expiry_days"] = config["cookie"].get("expiry_days", COOKIE_EXPIRY_DAYS)
        st.session_state["_auth_config"] = config
        st.session_state["authenticator"] = stauth.Authenticate(
            config["credentials"],
            config["cookie"]["name"],
            config["cookie"]["key"],
            config["cookie"]["expiry_days"],
        )
    return st.session_state["authenticator"]


def require_login() -> tuple[str, str, list[str]]:
    """Render the login form and stop the page if the user is not authenticated.

    Returns ``(name, username, roles)`` on success.
    """
    authenticator = get_authenticator()
    authenticator.login(location="main")

    if st.session_state.get("authentication_status") is False:
        st.error("使用者名稱或密碼錯誤 / Invalid username or password.")
        st.stop()

    if st.session_state.get("authentication_status") is None:
        st.info("請輸入帳號密碼登入 / Please log in to continue.")
        st.stop()

    username = st.session_state.get("username", "")
    name = st.session_state.get("name", username)

    config = st.session_state.get("_auth_config", {})
    user_record = config.get("credentials", {}).get("usernames", {}).get(username, {})
    roles = user_record.get("roles", ["viewer"])
    st.session_state["role"] = roles[0] if roles else "viewer"
    st.session_state["roles"] = roles

    with st.sidebar:
        st.markdown(f"**{name}**  \n`{st.session_state['role']}`")
        authenticator.logout("登出 / Logout", location="sidebar")

    return name, username, roles
