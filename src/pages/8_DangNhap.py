import streamlit as st
import time
from auth import authenticate_user, login_user, logout, get_current_user

st.set_page_config(page_title="Đăng nhập", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@200..900&display=swap');

/* ── Reset ── */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
#MainMenu { display: none !important; }
header { display: none !important; }
footer { display: none !important; }
.stAppToolbar { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Full viewport center ── */
[data-testid="stAppViewContainer"] {
    min-height: 100dvh !important;
    background: #f0ede8 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.stApp { background: #f0ede8 !important; }
section.main {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 20px !important;
    width: 100% !important;
}

/* ── Centered card ── */
.block-container {
    padding: 44px 40px !important;
    max-width: 400px !important;
    width: 100% !important;
    background: #ffffff !important;
    border: 1px solid rgba(0,0,0,0.04) !important;
    border-radius: var(--radius-xl) !important;
    box-shadow: 0 20px 60px -20px rgba(0,0,0,0.08) !important;
    animation: card-in 0.5s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes card-in {
    from { opacity: 0; transform: translateY(12px) scale(0.99); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── Brand ── */
.brand-logo {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
}
.brand-wordmark {
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    font-size: 28px;
    line-height: 1.1;
    letter-spacing: -0.03em;
    color: #1c1917;
    text-align: center;
    margin: 0 0 8px 0;
}
.brand-tagline {
    font-family: 'Outfit', sans-serif;
    font-weight: 400;
    font-size: 13px;
    line-height: 1.5;
    color: #6b6560;
    text-align: center;
    margin: 0 auto 24px auto;
    max-width: 280px;
}
.brand-divider {
    width: 32px;
    height: 2px;
    background: #5b8c7a;
    margin: 0 auto 28px auto;
    border-radius: 1px;
}

/* ── Form title ── */
.form-title {
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    font-size: 18px;
    color: #1c1917;
    text-align: center;
    margin: 0 0 24px 0;
}

/* ── TextInput ── */
div[data-testid="stTextInput"] {
    margin-bottom: 6px;
}
div[data-testid="stTextInput"] label p {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    color: #6b6560 !important;
}
div[data-testid="stTextInput"] input {
    font-family: 'Outfit', sans-serif !important;
    height: 46px !important;
    border-radius: 10px !important;
    border: 1px solid #d4d0c8 !important;
    background: #fcfcfb !important;
    color: #1c1917 !important;
    padding: 0 16px !important;
    font-size: 15px !important;
    font-weight: 400 !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #5b8c7a !important;
    box-shadow: 0 0 0 3px rgba(91,140,122,0.12) !important;
}
div[data-testid="stTextInput"] input:hover {
    border-color: #bbb6ae !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: #b5b0a8 !important;
    font-weight: 400 !important;
}

/* ── Primary button ── */
button[kind="primary"],
button[data-testid="baseButton-primary"] {
    height: 46px !important;
    border-radius: 10px !important;
    border: none !important;
    background: #5b8c7a !important;
    color: #ffffff !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    font-size: 15px !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease !important;
    cursor: pointer !important;
}
button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(91,140,122,0.18) !important;
    background: #4d7d6b !important;
}
button[kind="primary"]:active,
button[data-testid="baseButton-primary"]:active {
    transform: scale(0.98) !important;
}

/* ── Alerts ── */
[data-testid="stAlertContainer"] {
    border-radius: 10px !important;
    border: none !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 14px !important;
    margin-top: 8px !important;
}
[data-testid="stAlertContainer"] svg { display: none; }

/* ── Meta footer ── */
.meta-footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    color: #a8a29a;
    margin-top: 28px;
}
.meta-version {
    padding: 2px 8px;
    border: 1px solid #e0dcd4;
    border-radius: 4px;
    font-weight: 500;
}
.meta-status {
    display: flex;
    align-items: center;
    gap: 5px;
}
.meta-status::before {
    content: '';
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #5b8c7a;
    animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.35; }
}

/* ── Gap reset ── */
div[data-testid="stVerticalBlock"] > div:first-child {
    gap: 0 !important;
}

/* ── Mobile ── */
@media (max-width: 768px) {
    section.main { padding: 16px !important; }
    .block-container { padding: 32px 24px !important; border-radius: 16px !important; }
}
</style>
""", unsafe_allow_html=True)

user = get_current_user()

if user:
    st.markdown("""
    <div class="brand-logo">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <path d="M24 6L38 24L24 42L10 24L24 6Z" stroke="#5b8c7a" stroke-width="1.2" fill="none"/>
            <path d="M24 14L31 24L24 34L17 24L24 14Z" fill="rgba(91,140,122,0.15)"/>
        </svg>
    </div>
    <h1 class="brand-wordmark">H\u1ec7 th\u1ed1ng<br>\u0110\u1ecbnh m\u1ee9c T04</h1>
    <p class="brand-tagline">Qu\u1ea3n l\u00fd ch\u1ebf \u0111\u1ed9 l\u00e0m vi\u1ec7c nh\u00e0 gi\u00e1o</p>
    <div class="brand-divider"></div>
    """, unsafe_allow_html=True)

    role_labels = {
        "admin": "Qu\u1ea3n tr\u1ecb vi\u00ean",
        "head_dept": "Tr\u01b0\u1edfng Khoa / B\u1ed9 m\u00f4n"
    }
    role_label = role_labels.get(user["role"], "Ng\u01b0\u1eddi d\u00f9ng")

    st.markdown(f"""
    <div style="text-align:center">
        <svg width="64" height="64" viewBox="0 0 64 64" style="margin-bottom:12px">
            <circle cx="32" cy="32" r="32" fill="rgba(91,140,122,0.08)"/>
            <circle cx="32" cy="24" r="11" fill="rgba(91,140,122,0.5)"/>
            <path d="M12 54c0-11 9-20 20-20s20 9 20 20" fill="rgba(91,140,122,0.5)"/>
        </svg>
        <p style="font-family:'Outfit',sans-serif;font-weight:600;font-size:18px;color:#1c1917;margin:0 0 4px 0">{user["username"]}</p>
        <p style="font-family:'Outfit',sans-serif;font-weight:500;font-size:13px;color:#5b8c7a;margin:0 0 2px 0">{role_label}</p>
        {f'<p style="font-family:\'Outfit\',sans-serif;font-size:12px;color:#6b6560;margin:0 0 24px 0">{user["department_name"]}</p>' if user.get("department_name") else '<div style="height:18px"></div>'}
    </div>
    """, unsafe_allow_html=True)

    if st.button("\u0110\u0103ng xu\u1ea5t", type="primary", use_container_width=True, key="logout_btn"):
        logout()
        st.switch_page("pages/8_DangNhap.py")

else:
    st.markdown("""
    <div class="brand-logo">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <path d="M24 6L38 24L24 42L10 24L24 6Z" stroke="#5b8c7a" stroke-width="1.2" fill="none"/>
            <path d="M24 14L31 24L24 34L17 24L24 14Z" fill="rgba(91,140,122,0.15)"/>
        </svg>
    </div>
    <h1 class="brand-wordmark">H\u1ec7 th\u1ed1ng<br>\u0110\u1ecbnh m\u1ee9c T04</h1>
    <p class="brand-tagline">Qu\u1ea3n l\u00fd ch\u1ebf \u0111\u1ed9 l\u00e0m vi\u1ec7c nh\u00e0 gi\u00e1o theo Quy \u0111\u1ecbnh T04</p>
    <div class="brand-divider"></div>
    <p class="form-title">\u0110\u0103ng nh\u1eadp</p>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "T\u00ean \u0111\u0103ng nh\u1eadp",
            placeholder="Nh\u1eadp t\u00ean \u0111\u0103ng nh\u1eadp...",
            key="login_user"
        )
        password = st.text_input(
            "M\u1eadt kh\u1ea9u",
            type="password",
            placeholder="Nh\u1eadp m\u1eadt kh\u1ea9u...",
            key="login_pass"
        )

        submitted = st.form_submit_button(
            "\u0110\u0103ng nh\u1eadp",
            type="primary",
            use_container_width=True
        )

        if submitted:
            if not username or not password:
                st.error("Vui l\u00f2ng nh\u1eadp \u0111\u1ea7y \u0111\u1ee7 th\u00f4ng tin.")
            else:
                res = authenticate_user(username, password)
                if res:
                    if isinstance(res, dict) and res.get("error") == "teacher_disabled":
                        st.error("T\u00e0i kho\u1ea3n Gi\u1ea3ng vi\u00ean ch\u01b0a \u0111\u01b0\u1ee3c k\u00edch ho\u1ea1t.")
                    else:
                        login_user(res)
                        st.success("\u0110\u0103ng nh\u1eadp th\u00e0nh c\u00f4ng")
                        time.sleep(0.5)
                        st.switch_page("app.py")
                else:
                    st.error("Sai t\u00ean \u0111\u0103ng nh\u1eadp ho\u1eb7c m\u1eadt kh\u1ea9u.")

    st.markdown("""
    <div class="meta-footer">
        <span class="meta-version">v2.0</span>
        <span class="meta-status">H\u1ec7 th\u1ed1ng ho\u1ea1t \u0111\u1ed9ng</span>
    </div>
    """, unsafe_allow_html=True)
