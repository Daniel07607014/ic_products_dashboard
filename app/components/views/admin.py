from __future__ import annotations

import streamlit as st

from config.settings import AUTH_CONFIG_PATH, DATA_BACKEND


def _refresh_auth_state() -> None:
    """Force streamlit-authenticator to rebuild credentials on next rerun."""
    for key in ("authenticator", "_auth_config"):
        st.session_state.pop(key, None)


def _render_admin_mysql() -> None:
    from src.data.users import create_user, fetch_all_users, reset_password, set_active

    st.markdown("### 使用者管理 / User management（MySQL）")

    try:
        users = fetch_all_users()
    except Exception as exc:
        st.error(f"無法讀取 users 資料表 / Cannot read users table: {exc}")
        return

    st.dataframe(
        [
            {
                "username": u["username"],
                "name": u["name"],
                "email": u["email"],
                "role": u["role"],
                "啟用 / active": bool(u["is_active"]),
                "建立時間 / created": u["created_at"],
            }
            for u in users
        ],
        use_container_width=True,
    )

    tab_add, tab_toggle, tab_pw = st.tabs(
        ["➕ 新增使用者", "🔄 啟用 / 停用", "🔑 重設密碼"]
    )

    with tab_add:
        with st.form("add_user", clear_on_submit=True):
            username = st.text_input("帳號 / Username")
            name = st.text_input("顯示名稱 / Display name")
            email = st.text_input("Email（選填）")
            password = st.text_input("密碼 / Password", type="password")
            role = st.selectbox("角色 / Role", ["viewer", "admin"])
            if st.form_submit_button("建立 / Create"):
                try:
                    create_user(username.strip(), name.strip(), email.strip(), password, role)
                except Exception as exc:
                    st.error(f"建立失敗 / Failed: {exc}")
                else:
                    _refresh_auth_state()
                    st.success(f"已建立 {username}，登入頁即刻生效。")
                    st.rerun()

    with tab_toggle:
        current = st.session_state.get("username", "")
        others = [u for u in users if u["username"] != current]
        if not others:
            st.info("沒有其他使用者可操作（不能停用自己）。")
        else:
            target = st.selectbox(
                "使用者 / User",
                options=[u["username"] for u in others],
                format_func=lambda u: f"{u}（{'啟用中' if next(x for x in others if x['username'] == u)['is_active'] else '已停用'}）",
                key="toggle_target",
            )
            info = next(u for u in others if u["username"] == target)
            active_now = bool(info["is_active"])
            label = "停用 / Deactivate" if active_now else "啟用 / Activate"
            if st.button(label, key="toggle_btn"):
                set_active(target, not active_now)
                _refresh_auth_state()
                st.success(f"{target} 已{'停用' if active_now else '啟用'}。")
                st.rerun()

    with tab_pw:
        target = st.selectbox(
            "使用者 / User", options=[u["username"] for u in users], key="pw_target"
        )
        new_pw = st.text_input("新密碼 / New password", type="password", key="pw_value")
        if st.button("重設 / Reset", key="pw_btn"):
            try:
                reset_password(target, new_pw)
            except Exception as exc:
                st.error(f"重設失敗 / Failed: {exc}")
            else:
                _refresh_auth_state()
                st.success(f"{target} 的密碼已更新。")


def _render_admin_yaml() -> None:
    st.markdown(
        f"""
        ### 現有帳號 / Current users

        使用者定義於 `{AUTH_CONFIG_PATH}`（csv/yaml 模式為唯讀）。新增或修改請：

        1. 執行 `python deploy/scripts/hash_password.py` 產生 bcrypt hash
        2. 編輯 `config/auth_config.yaml` 填入使用者資料
        3. 重啟 Streamlit 讓變更生效

        （將 `.env` 的 `DATA_BACKEND` 設為 `mysql` 可解鎖 UI 內管理。）
        """
    )

    config = st.session_state.get("_auth_config", {})
    users = config.get("credentials", {}).get("usernames", {})
    rows = [
        {"username": u, "name": info.get("name"), "email": info.get("email"), "roles": ", ".join(info.get("roles", []))}
        for u, info in users.items()
    ]
    st.dataframe(rows, use_container_width=True)


def render_admin() -> None:
    if DATA_BACKEND == "mysql":
        _render_admin_mysql()
    else:
        _render_admin_yaml()
