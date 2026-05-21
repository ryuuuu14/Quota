import streamlit as st

def render_status_bar(name, title, dept, roles_count_or_list, events_count_or_list):
    if isinstance(roles_count_or_list, list):
        roles = roles_count_or_list
    elif isinstance(roles_count_or_list, (int, float)):
        roles = [f"{roles_count_or_list} Chức vụ"] if roles_count_or_list > 0 else []
    else:
        roles = [str(roles_count_or_list)] if roles_count_or_list else []

    if isinstance(events_count_or_list, list):
        events = events_count_or_list
    elif isinstance(events_count_or_list, (int, float)):
        events = [f"{events_count_or_list} Sự kiện"] if events_count_or_list > 0 else []
    else:
        events = [str(events_count_or_list)] if events_count_or_list else []

    roles_html = ""
    if roles:
        for r in roles:
            roles_html += f"""<span class="md-chip md-chip-primary" style="margin-right: 4px; margin-bottom: 4px; display: inline-flex; align-items: center;"><span class="material-symbols-outlined" style="font-size: 14px; margin-right: 4px;">badge</span> {r}</span>"""
    else:
        roles_html = """<span class="md-chip" style="background-color: var(--md-surface-container-high); color: var(--md-on-surface-variant); opacity: 0.8; display: inline-flex; align-items: center;">Không giữ chức vụ</span>"""

    events_html = ""
    if events:
        for e in events:
            events_html += f"""<span class="md-chip md-chip-green" style="margin-right: 4px; margin-bottom: 4px; display: inline-flex; align-items: center;"><span class="material-symbols-outlined" style="font-size: 14px; margin-right: 4px;">event</span> {e}</span>"""
    else:
        events_html = """<span class="md-chip" style="background-color: var(--md-surface-container-high); color: var(--md-on-surface-variant); opacity: 0.8; display: inline-flex; align-items: center;">Không có sự kiện miễn giảm</span>"""

    st.markdown(f"""
<div class="md-status-bar" style="display: flex; flex-direction: column; gap: 12px; align-items: flex-start; width: 100%;">
<div style="display: flex; gap: 32px; align-items: center; flex-wrap: wrap; width: 100%;">
<div>
<div class="md-section-label">Nhà giáo</div>
<div style="color: var(--md-on-surface); font-weight: 700; font-size: 1.2rem; margin-top: 2px;">{name}</div>
</div>
<div style="border-left: 1px solid var(--md-outline-variant); height: 32px;"></div>
<div>
<div class="md-section-label">Chức danh</div>
<div style="color: var(--md-on-surface); font-weight: 600; font-size: 1rem; margin-top: 2px;">{title}</div>
</div>
<div style="border-left: 1px solid var(--md-outline-variant); height: 32px;"></div>
<div>
<div class="md-section-label">Đơn vị công tác</div>
<div style="color: var(--md-on-surface); font-weight: 600; font-size: 1rem; margin-top: 2px;">{dept}</div>
</div>
</div>
<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; width: 100%;">
<div style="display: flex; align-items: center; gap: 4px; margin-right: 12px; flex-wrap: wrap;">
<span style="font-size: 0.85rem; font-weight: 600; color: var(--md-on-surface-variant);">Chức vụ:</span>
{roles_html}
</div>
<div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">
<span style="font-size: 0.85rem; font-weight: 600; color: var(--md-on-surface-variant);">Miễn giảm hiện tại:</span>
{events_html}
</div>
</div>
</div>
""", unsafe_allow_html=True)


def render_empty_state(message):
    st.markdown(f"""
<div style="
    background-color: var(--md-surface-container-low);
    padding: 40px 32px;
    border-radius: var(--radius-lg);
    text-align: center;
    color: var(--md-on-surface-variant);
    border: 1px dashed var(--md-outline-variant);
    margin: 24px 0;
    font-size: 0.95rem;
    line-height: 1.5;
">
    <span class="material-symbols-outlined" style="font-size: 48px; color: var(--md-outline); margin-bottom: 12px;">inbox</span>
    <div>{message}</div>
</div>
    """, unsafe_allow_html=True)


def render_warning_state(message):
    st.markdown(f"""
<div style="
    background-color: var(--md-amber-bg);
    padding: 16px 20px;
    border-radius: var(--radius-md);
    border-left: 4px solid var(--md-amber);
    color: #78350f;
    margin: 20px 0;
    font-size: 0.95rem;
    line-height: 1.5;
">
    <strong style="color: var(--md-amber);">Lưu ý:</strong> {message}
</div>
    """, unsafe_allow_html=True)


def render_metric_card(title, value, delta=None, icon=None):
    delta_html = ""
    if delta:
        is_positive = delta.startswith("+")
        bg = "var(--md-green-bg)" if is_positive else "var(--md-red-bg)"
        color = "var(--md-green)" if is_positive else "var(--md-red)"
        delta_html = f'<span style="background-color: {bg}; color: {color}; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: var(--radius-sm); margin-left: 8px;">{delta}</span>'

    icon_html = ""
    if icon:
        icon_html = f'<span class="material-symbols-outlined" style="color: var(--md-on-surface-variant); font-size: 20px;">{icon}</span>'

    # Do not indent HTML block lines to avoid markdown code block parsing
    st.markdown(f"""
<div style="background: var(--md-surface-container-lowest); padding: 24px; border-radius: var(--radius-lg); box-shadow: var(--shadow-elevated); border: 1px solid var(--md-outline-variant); display: flex; flex-direction: column; gap: 12px;">
<div style="display: flex; align-items: baseline; justify-content: space-between;">
<span style="color: var(--md-on-surface); font-size: 2.5rem; font-weight: 800; font-family: var(--font-family); letter-spacing: -0.02em;">{value}</span>{delta_html}
</div>
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="color: var(--md-on-surface-variant); font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">{title}</span>{icon_html}
</div>
</div>
""", unsafe_allow_html=True)


def render_chip(label, variant="primary", icon=None):
    variant_class = {
        "primary": "md-chip-primary",
        "green": "md-chip-green",
        "red": "md-chip-red",
        "amber": "md-chip-amber",
        "tertiary": "md-chip-tertiary",
    }.get(variant, "md-chip-primary")
    icon_html = f'<span class="material-symbols-outlined" style="font-size: 14px; margin-right: 4px;">{icon}</span>' if icon else ""
    return f'<span class="md-chip {variant_class}">{icon_html}{label}</span>'


def render_card(content, extra_class=""):
    return f'<div class="md-card {extra_class}">{content}</div>'


def render_sidebar(active_page="home"):
    # 1. Hide default navigation
    st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)
    
    # 2. Inject global fonts, Material symbols and theme styles
    st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,0&display=swap" rel="stylesheet">
<style>
    :root {
        --md-primary: #003f87;
        --md-primary-container: #0056b3;
        --md-on-primary: #ffffff;
        --md-on-primary-container: #bbd0ff;
        --md-primary-fixed: #d7e2ff;
        --md-primary-fixed-dim: #acc7ff;
        --md-surface: #f9f9ff;
        --md-surface-dim: #d9d9e2;
        --md-surface-container-lowest: #ffffff;
        --md-surface-container-low: #f2f3fc;
        --md-surface-container: #ededf6;
        --md-surface-container-high: #e7e8f0;
        --md-surface-container-highest: #e1e2ea;
        --md-on-surface: #191c21;
        --md-on-surface-variant: #424752;
        --md-outline: #727784;
        --md-outline-variant: #c2c6d4;
        --md-secondary: #575f67;
        --md-secondary-container: #d8e1ea;
        --md-tertiary: #722b00;
        --md-tertiary-container: #983c00;
        --md-error: #ba1a1a;
        --md-error-container: #ffdad6;
        --md-on-error: #ffffff;
        --md-on-error-container: #93000a;
        --md-inverse-surface: #2e3037;
        --md-inverse-on-surface: #f0f0f9;
        --md-inverse-primary: #acc7ff;
        --md-green: #047857;
        --md-green-bg: #ecfdf5;
        --md-red: #b91c1c;
        --md-red-bg: #fef2f2;
        --md-amber: #d97706;
        --md-amber-bg: #fffbeb;
        --radius-sm: 4px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-xl: 16px;
        --radius-full: 9999px;
        --shadow-card: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        --shadow-elevated: 0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.05);
        --font-family: 'Inter', sans-serif;
    }

    html, body, #root, .stApp {
        font-family: var(--font-family) !important;
        background-color: var(--md-surface) !important;
        color: var(--md-on-surface) !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-family) !important;
        color: var(--md-on-surface) !important;
    }
    h1 {
        font-size: 36px !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.2 !important;
    }
    h2 { font-size: 24px !important; font-weight: 600 !important; line-height: 1.3 !important; }
    h3 { font-size: 18px !important; font-weight: 600 !important; line-height: 1.4 !important; }

    section[data-testid="stSidebar"] {
        background-color: var(--md-surface-container-low) !important;
        border-right: 1px solid var(--md-outline-variant) !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] .st-emotion-cache-1wrcr25,
    section[data-testid="stSidebar"] .st-emotion-cache-1gv5dpq {
        background-color: transparent !important;
    }
    section[data-testid="stSidebar"] a {
        font-family: var(--font-family) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        font-size: 14px !important;
        color: var(--md-on-surface-variant) !important;
    }
    section[data-testid="stSidebar"] .st-emotion-cache-16idsys p {
        font-size: 16px !important;
        font-family: var(--font-family) !important;
    }

    .stButton > button {
        font-family: var(--font-family) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        border: 1px solid var(--md-outline-variant) !important;
    }
    .stButton > button:hover {
        transform: scale(0.98) !important;
    }
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid var(--md-outline) !important;
        color: var(--md-on-surface) !important;
    }

    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input {
        font-family: var(--font-family) !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--md-outline-variant) !important;
        font-size: 16px !important;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus, .stDateInput input:focus {
        border-color: var(--md-primary-container) !important;
        box-shadow: 0 0 0 2px var(--md-primary-fixed) !important;
    }
    .stSelectbox label, .stTextInput label, .stDateInput label, .stNumberInput label, .stRadio label, .stMultiSelect label, .stSlider label {
        font-family: var(--font-family) !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: var(--md-on-surface) !important;
        text-transform: none !important;
        letter-spacing: normal !important;
    }

    .stTabs {
        background-color: transparent !important;
    }
    .stTabs div[data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: transparent !important;
        border-bottom: none !important;
    }
    .stTabs button[data-baseweb="tab"] {
        font-family: var(--font-family) !important;
        font-size: 16px !important;
    }
    .stTabs button p {
        font-size: 15px !important;
        font-weight: 600 !important;
    }

    .stNumberInput input, .stMultiSelect div[data-baseweb="select"] > div {
        font-family: var(--font-family) !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--md-outline-variant) !important;
    }

    .md-card {
        background-color: var(--md-surface-container-lowest) !important;
        border: 1px solid var(--md-outline-variant) !important;
        border-radius: var(--radius-lg) !important;
        padding: 24px !important;
        box-shadow: var(--shadow-card) !important;
        margin-bottom: 16px !important;
    }

    .md-chip {
        display: inline-flex !important;
        align-items: center !important;
        padding: 5px 14px !important;
        border-radius: var(--radius-full) !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: none !important;
        white-space: nowrap !important;
    }
    .md-chip-primary {
        background-color: var(--md-primary-fixed) !important;
        color: var(--md-primary) !important;
    }
    .md-chip-green {
        background-color: var(--md-green-bg) !important;
        color: var(--md-green) !important;
    }
    .md-chip-red {
        background-color: var(--md-red-bg) !important;
        color: var(--md-red) !important;
    }
    .md-chip-amber {
        background-color: var(--md-amber-bg) !important;
        color: var(--md-amber) !important;
    }
    .md-chip-tertiary {
        background-color: var(--md-secondary-container) !important;
        color: var(--md-secondary) !important;
    }
    
    .stButton button[aria-label="Xóa"],
    .stButton button[aria-label*="Xóa"],
    .stButton button[aria-label*="xóa"],
    .stButton button[aria-label*="Xoá"],
    .stButton button[aria-label*="xoá"] {
        background-color: var(--md-red-bg) !important;
        color: var(--md-red) !important;
        border: 1px solid var(--md-red) !important;
    }
    .stButton button[aria-label="Xóa"]:hover,
    .stButton button[aria-label*="Xóa"]:hover,
    .stButton button[aria-label*="Xoá"]:hover {
        background-color: var(--md-error-container) !important;
        color: var(--md-on-error-container) !important;
    }
    .md-status-bar {
        background-color: var(--md-surface-container-low) !important;
        border: 1px solid var(--md-outline-variant) !important;
        border-radius: var(--radius-lg) !important;
        padding: 16px 24px !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        box-shadow: var(--shadow-card) !important;
    }
    .md-section-label {
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: var(--md-on-surface-variant) !important;
    }
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    [data-testid="stPageLink"] {
        padding: 0 !important;
        margin: 2px 0 !important;
    }
    [data-testid="stPageLink"] > a {
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        padding: 10px 16px !important;
        border-radius: var(--radius-md) !important;
        text-decoration: none !important;
        font-size: 15px !important;
        font-family: var(--font-family) !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
        background-color: transparent !important;
        border: none !important;
        width: 100% !important;
        box-sizing: border-box !important;
        color: var(--md-on-surface-variant) !important;
    }
    [data-testid="stPageLink"] > a:hover {
        background-color: var(--md-surface-container-high) !important;
        color: var(--md-on-surface) !important;
    }
    [data-testid="stPageLink"] > a[aria-current="page"] {
        background-color: var(--md-primary-container) !important;
        color: var(--md-on-primary) !important;
        font-weight: 600 !important;
    }
    [data-testid="stPageLink"] p {
        color: inherit !important;
        font-size: 15px !important;
        font-weight: inherit !important;
        margin: 0 !important;
    }
    [data-testid="stPageLink"] span {
        color: inherit !important;
        font-size: 20px !important;
    }
</style>
""", unsafe_allow_html=True)

    # 4. Render HTML sidebar
    with st.sidebar:
        st.markdown(f"""
<div style="padding: 8px 16px 24px 16px; border-bottom: 1px solid var(--md-outline-variant); margin-bottom: 16px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="
            width: 40px; height: 40px;
            background: linear-gradient(135deg, var(--md-primary-container), var(--md-primary));
            border-radius: var(--radius-md);
            display: flex; align-items: center; justify-content: center;
            color: var(--md-on-primary);
            font-size: 20px;
        ">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">school</span>
        </div>
        <div>
            <div style="font-weight: 700; font-size: 16px; color: var(--md-on-surface); line-height: 1.2;">Quản lý T04</div>
            <div style="font-size: 11px; color: var(--md-on-surface-variant); letter-spacing: 0.03em;">Hệ thống định mức</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        st.page_link("app.py", label="Trang chủ", icon=":material/home:")
        st.page_link("pages/1_Dashboard.py", label="Bảng điều khiển", icon=":material/dashboard:")
        st.page_link("pages/2_QuanLyCanBo.py", label="Quản lý Cán bộ", icon=":material/groups:")
        st.page_link("pages/3_NhatKyHoatDong.py", label="Nhật ký Hoạt động", icon=":material/edit_note:")
        st.page_link("pages/4_CaiDatHeThong.py", label="Cài đặt Hệ thống", icon=":material/settings:")

        st.markdown("""
<div style="
    margin-top: 32px;
    padding: 16px;
    background-color: var(--md-primary-fixed);
    border-radius: var(--radius-md);
    font-size: 12px;
    color: var(--md-primary);
    line-height: 1.5;
    display: flex;
    align-items: start;
    gap: 8px;
">
    <span class="material-symbols-outlined" style="font-size: 16px; margin-top: 1px;">info</span>
    <div>v2.0 — Hệ thống định mức T04</div>
</div>
""", unsafe_allow_html=True)
