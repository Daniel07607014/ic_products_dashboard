from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.permissions import require_role  # noqa: E402
from app.components.views.admin import render_admin  # noqa: E402

require_role("admin")

st.title("權限管理 · Admin")

render_admin()
