import streamlit as st
import time
from auth import authenticate_user, login_user, logout, get_current_user
import components
_get_logo_base64 = getattr(components, "_get_logo_base64", None)
if _get_logo_base64 is None:
    import importlib
    importlib.reload(components)
    _get_logo_base64 = getattr(components, "_get_logo_base64", lambda: "")

st.set_page_config(
    page_title="Đăng nhập - Hệ Thống Quản lý Chế độ làm việc - Đại học An ninh nhân dân", layout="wide", initial_sidebar_state="collapsed"
)

st.markdown(
    """
<style>
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
#MainMenu { display: none !important; }
header { display: none !important; }
footer { display: none !important; }
.stAppToolbar { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

[data-testid="stAppViewContainer"] {
    min-height: 100dvh !important;
    background: #800020 !important;
}
.stApp { background: #800020 !important; }
section.main {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 100vh !important;
    width: 100% !important;
    padding: 0 !important;
}
section.main > div {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    min-height: 100vh !important;
    padding: 20px !important;
    box-sizing: border-box !important;
}

.block-container {
    width: 100% !important;
    background: #FDF8F3 !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    border-radius: 24px !important;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.30) !important;
    animation: card-in 0.5s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes card-in {
    from { opacity: 0; transform: translateY(12px) scale(0.99); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}

.brand-logo {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
}
.brand-wordmark {
    font-family: 'Be Vietnam Pro', sans-serif;
    font-weight: 800;
    font-size: 26px;
    line-height: 1.2;
    letter-spacing: -0.03em;
    color: #1A1A1A;
    text-align: center;
    margin: 0 0 4px 0;
}
.brand-tagline {
    font-family: 'Be Vietnam Pro', sans-serif;
    font-weight: 400;
    font-size: 13px;
    line-height: 1.5;
    color: #5C5248;
    text-align: center;
    margin: 0 auto 24px auto;
    max-width: 280px;
}
.brand-divider {
    width: 48px;
    height: 4px;
    background: linear-gradient(90deg, #007855, #005C41);
    border-radius: 4px;
    margin: 0 auto 32px auto;
}
.form-title {
    font-family: 'Be Vietnam Pro', sans-serif;
    font-weight: 600;
    font-size: 18px;
    color: #1A1A1A;
    text-align: center;
    margin: 0 0 24px 0;
}
div[data-testid="stTextInput"] {
    margin-bottom: 6px;
}
div[data-testid="stTextInput"] label p {
    font-family: 'Be Vietnam Pro', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    color: #5C5248 !important;
}
div[data-testid="stTextInput"] input {
    font-family: 'Be Vietnam Pro', sans-serif !important;
    height: 46px !important;
    border-radius: 10px !important;
    border: 1px solid #D4C9BC !important;
    background: #FFFFFF !important;
    color: #1A1A1A !important;
    padding: 0 16px !important;
    font-size: 15px !important;
    font-weight: 400 !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #006747 !important;
    box-shadow: 0 0 0 3px rgba(0, 103, 71, 0.12) !important;
}
div[data-testid="stTextInput"] input:hover {
    border-color: #B8AD9E !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: #B8AD9E !important;
    font-weight: 400 !important;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"],
div[data-testid="stFormSubmitButton"] > button,
button[kind="primary"],
button[data-testid="baseButton-primary"] {
    height: 46px !important;
    border-radius: 10px !important;
    border: none !important;
    background: #006747 !important;
    color: #FFFFFF !important;
    font-family: 'Be Vietnam Pro', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease !important;
    cursor: pointer !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover,
div[data-testid="stFormSubmitButton"] > button:hover,
button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(0, 103, 71, 0.25) !important;
    background: #005C35 !important;
}
.stButton > button[kind="primary"]:active,
.stButton > button[data-testid="baseButton-primary"]:active,
div[data-testid="stFormSubmitButton"] > button:active,
button[kind="primary"]:active,
button[data-testid="baseButton-primary"]:active {
    transform: scale(0.98) !important;
}

[data-testid="stAlertContainer"] {
    border-radius: 10px !important;
    border: none !important;
    font-family: 'Be Vietnam Pro', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 14px !important;
    margin-top: 8px !important;
}
[data-testid="stAlertContainer"] svg { display: none; }

.meta-footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    font-family: 'Be Vietnam Pro', sans-serif;
    font-size: 11px;
    color: #B8AD9E;
    margin-top: 28px;
}
.meta-version {
    padding: 2px 8px;
    border: 1px solid #D4C9BC;
    border-radius: 4px;
    font-weight: 600;
    color: #5C5248;
}
.meta-status {
    display: flex;
    align-items: center;
    gap: 5px;
    color: #5C5248;
}
.meta-status::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #006747;
    animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.35; }
}

div[data-testid="stVerticalBlock"] > div:first-child {
    gap: 0 !important;
}
div[data-testid="stElementContainer"]:has(style) {
    display: none !important;
    margin: 0 !important;
    padding: 0 !important;
    height: 0 !important;
}
.block-container > div[data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

@media (max-width: 768px) {
    section.main { padding: 16px !important; }
    .block-container { padding: 32px 24px !important; border-radius: 16px !important; }
}
</style>
""",
    unsafe_allow_html=True,
)

user = get_current_user()

if user:
    st.markdown(
        """
        <style>
        .block-container {
            padding: 44px 40px !important;
            max-width: 400px !important;
            width: 100% !important;
            background: #FDF8F3 !important;
            border: 1px solid rgba(255, 255, 255, 0.10) !important;
            border-radius: 24px !important;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.30) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    logo_base64 = _get_logo_base64()
    logo_html = ""
    if logo_base64:
        logo_html = f'<img src="{logo_base64}" style="width: 72px; height: 72px; border-radius: 50%; object-fit: cover; border: 2.5px solid #006747;" />'
    else:
        logo_html = """
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <path d="M24 6L38 24L24 42L10 24L24 6Z" stroke="#006747" stroke-width="1.2" fill="none"/>
            <path d="M24 14L31 24L24 34L17 24L24 14Z" fill="rgba(0,103,71,0.15)"/>
        </svg>
        """

    st.markdown(
        f"""
    <div style="display: flex; flex-direction: column; align-items: center; text-align: center; width: 100%;">
        <div class="brand-logo">
            {logo_html}
        </div>
        <h1 class="brand-wordmark">Hệ Thống Quản lý<br>Chế độ làm việc</h1>
        <p class="brand-tagline">Đại học An ninh nhân dân</p>
        <div class="brand-divider"></div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    role_labels = {
        "admin": "Quản trị viên",
        "head_dept": "Trưởng Khoa / Bộ môn",
    }
    role_label = role_labels.get(user["role"], "Người dùng")

    st.markdown(
        f"""
    <div style="text-align:center">
        <svg width="64" height="64" viewBox="0 0 64 64" style="margin-bottom:12px">
            <circle cx="32" cy="32" r="32" fill="rgba(0,103,71,0.08)"/>
            <circle cx="32" cy="24" r="11" fill="rgba(0,103,71,0.5)"/>
            <path d="M12 54c0-11 9-20 20-20s20 9 20 20" fill="rgba(0,103,71,0.5)"/>
        </svg>
        <p style="font-family:'Be Vietnam Pro',sans-serif;font-weight:600;font-size:18px;color:#1A1A1A;margin:0 0 4px 0">{user["username"]}</p>
        <p style="font-family:'Be Vietnam Pro',sans-serif;font-weight:600;font-size:13px;color:#FFC107;margin:0 0 2px 0">{role_label}</p>
        {f"<p style=\"font-family:'Be Vietnam Pro',sans-serif;font-size:12px;color:#5C5248;margin:0 0 24px 0\">{user["department_name"]}</p>" if user.get("department_name") else '<div style="height:18px"></div>'}
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button(
        "Đăng xuất",
        type="primary",
        use_container_width=True,
        key="logout_btn",
    ):
        logout()
        st.switch_page("pages/8_DangNhap.py")

else:
    st.markdown(
        """
        <style>
        .block-container {
            padding: 0 !important;
            max-width: 850px !important;
            width: 100% !important;
            background: #FDF8F3 !important;
            border: 1px solid rgba(255, 255, 255, 0.10) !important;
            border-radius: 24px !important;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.30) !important;
            overflow: hidden !important;
            margin: auto !important;
        }
        [data-testid="stHorizontalBlock"] {
            gap: 0 !important;
            margin: 0 !important;
            width: 100% !important;
        }
        [data-testid="stHorizontalBlock"] > div:nth-of-type(1) {
            background: linear-gradient(135deg, #005C41 0%, #003625 100%) !important;
            padding: 48px 40px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            color: #FFFFFF !important;
            min-height: 480px !important;
        }
        [data-testid="stHorizontalBlock"] > div:nth-of-type(2) {
            padding: 48px 40px !important;
            background: #FDF8F3 !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
        }
        .brand-panel-title {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-weight: 800;
            font-size: 28px;
            line-height: 1.25;
            letter-spacing: -0.02em;
            color: #FFFFFF;
            margin: 16px 0 8px 0;
            text-align: center;
        }
        .brand-panel-subtitle {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-weight: 600;
            font-size: 14px;
            color: #FFC107;
            margin: 0 0 20px 0;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            text-align: center;
        }
        .brand-panel-divider {
            width: 60px;
            height: 4px;
            background: #FFC107;
            border-radius: 2px;
            margin: 0 auto;
        }
        @media (max-width: 768px) {
            .block-container {
                max-width: 450px !important;
                margin: 10px !important;
            }
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
            [data-testid="stHorizontalBlock"] > div:nth-of-type(1) {
                width: 100% !important;
                min-height: auto !important;
                padding: 36px 24px !important;
            }
            [data-testid="stHorizontalBlock"] > div:nth-of-type(2) {
                width: 100% !important;
                padding: 36px 24px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1.2, 1])

    with col1:
        logo_base64 = _get_logo_base64()
        logo_html = ""
        if logo_base64:
            logo_html = f'<img src="{logo_base64}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2.5px solid #FFC107;" />'
        else:
            logo_html = """
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                <path d="M24 6L38 24L24 42L10 24L24 6Z" stroke="#FFC107" stroke-width="1.2" fill="none"/>
                <path d="M24 14L31 24L24 34L17 24L24 14Z" fill="rgba(255,193,7,0.15)"/>
            </svg>
            """
        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; align-items: center; text-align: center; width: 100%;">
                <div class="brand-logo">
                    {logo_html}
                </div>
                <h1 class="brand-panel-title">Hệ Thống Quản lý<br>Chế độ làm việc</h1>
                <p class="brand-panel-subtitle">Đại học An ninh nhân dân</p>
                <div class="brand-panel-divider"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown('<p class="form-title">Đăng nhập</p>', unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Tên đăng nhập",
                placeholder="Nhập tên đăng nhập...",
                key="login_user",
            )
            password = st.text_input(
                "Mật khẩu",
                type="password",
                placeholder="Nhập mật khẩu...",
                key="login_pass",
            )

            submitted = st.form_submit_button(
                "Đăng nhập", type="primary", use_container_width=True
            )

            if submitted:
                if not username or not password:
                    st.error("Vui lòng nhập đầy đủ thông tin.")
                else:
                    res = authenticate_user(username, password)
                    if res:
                        if isinstance(res, dict) and res.get("error") == "teacher_disabled":
                            st.error("Tài khoản Giảng viên chưa được kích hoạt.")
                        else:
                            login_user(res)
                            st.success("Đăng nhập thành công")
                            time.sleep(0.5)
                            st.switch_page("app.py")
                    else:
                        st.error("Sai tên đăng nhập hoặc mật khẩu.")

        st.markdown(
            """
            <div class="meta-footer">
                <span class="meta-version">v2.0</span>
                <span class="meta-status">Hệ thống hoạt động</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
