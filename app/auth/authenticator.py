"""streamlit-authenticator wrapper.

Auth flow with ``st.navigation``:

    main.py checks :func:`is_authenticated`. If false, ``st.navigation``
    only exposes a single page that calls :func:`render_login`. On
    success the login form causes a rerun and main.py switches to the
    full navigation. Pages themselves no longer render the login form —
    they just call :func:`require_role` (or :func:`current_user`) to
    read the signed-in user.
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
            "Run `python deploy/scripts/init_admin.py --username admin` to create one."
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


def is_authenticated() -> bool:
    """True once the user has passed the login form (or restored via cookie)."""
    get_authenticator()  # ensures cookie restore + session_state init
    return st.session_state.get("authentication_status") is True


def current_user() -> tuple[str, str, list[str]]:
    """Return ``(name, username, roles)`` for the signed-in user.

    Also caches the primary role at ``session_state['role']`` so
    :mod:`app.auth.permissions` can read it cheaply.
    """
    username = st.session_state.get("username", "")
    name = st.session_state.get("name", username)
    config = st.session_state.get("_auth_config", {})
    user_record = config.get("credentials", {}).get("usernames", {}).get(username, {})
    roles = user_record.get("roles", ["viewer"])
    st.session_state["role"] = roles[0] if roles else "viewer"
    st.session_state["roles"] = roles
    return name, username, roles


def render_login() -> None:
    """Standalone login page shown by ``st.navigation`` when unauthenticated."""
    st.title(":bar_chart: IC 產品毛利率 Dashboard")
    st.markdown("#### :lock: 登入 / Sign in")
    st.markdown("請輸入帳號密碼進入系統 / Enter your credentials to continue.")

    left, _ = st.columns([1, 1])
    with left:
        authenticator = get_authenticator()
        authenticator.login(location="main")

        status = st.session_state.get("authentication_status")
        if status is False:
            st.error("使用者名稱或密碼錯誤 / Invalid username or password.")
        elif status is None:
            st.info("尚未登入 / Please sign in above.")


def render_sidebar_user_info() -> None:
    """Show the user badge + logout button. Call once from main.py after login."""
    name, _, _ = current_user()
    role = st.session_state.get("role", "viewer")
    authenticator = get_authenticator()
    with st.sidebar:
        st.markdown(f"**{name}**  \n`{role}`")
        authenticator.logout("登出 / Logout", location="sidebar")
        st.markdown("---")


def require_login() -> tuple[str, str, list[str]]:
    """Backward-compat guard: stops the page if the user is not signed in.

    Prefer :func:`current_user` in pages — auth is now gated centrally in
    main.py via ``st.navigation``. Kept for scripts / notebooks that still
    call this directly.
    """
    if not is_authenticated():
        st.error("尚未登入 / Please log in first.")
        st.stop()
    return current_user()
