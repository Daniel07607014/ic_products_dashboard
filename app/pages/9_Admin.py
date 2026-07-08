from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.auth.authenticator import require_login  # noqa: E402
from app.auth.permissions import require_role  # noqa: E402
from config.settings import AUTH_CONFIG_PATH  # noqa: E402

st.set_page_config(page_title="Admin", page_icon=":lock:", layout="wide")
require_login()
require_role("admin")

st.title("Admin · 使用者管理")

st.markdown(
    f"""
    ### 現有帳號 / Current users

    使用者定義於 `{AUTH_CONFIG_PATH}`。新增或修改請：

    1. 執行 `python deploy/scripts/hash_password.py` 產生 bcrypt hash
    2. 編輯 `config/auth_config.yaml` 填入使用者資料
    3. 重啟 Streamlit 讓變更生效
    """
)

config = st.session_state.get("_auth_config", {})
users = config.get("credentials", {}).get("usernames", {})
rows = [
    {"username": u, "name": info.get("name"), "email": info.get("email"), "roles": ", ".join(info.get("roles", []))}
    for u, info in users.items()
]
st.dataframe(rows, use_container_width=True)

st.info(
    "TODO: 直接在 UI 上新增/停用使用者。目前為安全考量僅顯示唯讀資訊。"
)
