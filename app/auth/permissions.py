"""Role-based page guards. Each restricted page calls :func:`require_role` at top."""
from __future__ import annotations

import streamlit as st

ROLE_HIERARCHY = {"viewer": 0, "admin": 10}


def _current_role() -> str:
    return st.session_state.get("role", "viewer")


def has_role(required: str) -> bool:
    return ROLE_HIERARCHY.get(_current_role(), -1) >= ROLE_HIERARCHY.get(required, 999)


def require_role(required: str) -> None:
    """Stop the page with an error if the current user lacks ``required``."""
    if "authentication_status" not in st.session_state or not st.session_state.get("authentication_status"):
        st.error("尚未登入 / Please log in first.")
        st.stop()
    if not has_role(required):
        st.error(f"權限不足：需要 `{required}` 角色 / Access denied: requires `{required}` role.")
        st.stop()
