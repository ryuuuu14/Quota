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
        icon_html = f'<span class="material-symbols-outlined" style="color: var(--md-primary-fixed-dim); font-size: 24px;">{icon}</span>'

    # Do not indent HTML block lines to avoid markdown code block parsing
    st.markdown(f"""
<div class="md-card" style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 0px; padding: 20px !important;">
<div style="display: flex; align-items: baseline; justify-content: space-between;">
<span style="color: #ffffff; font-size: 2.2rem; font-weight: 800; font-family: var(--font-family); letter-spacing: -0.02em;">{value}</span>{delta_html}
</div>
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="color: var(--md-on-surface-variant); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">{title}</span>{icon_html}
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


def inject_premium_css():
    """
    Tiêm mã CSS thiết kế Pro-Max chứa các design tokens, glassmorphism,
    hiệu ứng 3D hover và hỗ trợ hiển thị trên thiết bị di động (Chế độ Sáng - Light Mode).
    """
    st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,0&display=swap" rel="stylesheet">
<style>
    :root {
        --md-primary: #0f4c81; /* Classic Premium Navy */
        --md-primary-container: #e3f2fd;
        --md-on-primary: #ffffff;
        --md-on-primary-container: #0f4c81;
        --md-primary-fixed: #e3f2fd;
        --md-primary-fixed-dim: #90caf9;
        --md-surface: #f8f9fa; /* Pure Light Slate Gray */
        --md-surface-dim: #f1f3f5;
        --md-surface-container-lowest: #ffffff; /* White background for cards */
        --md-surface-container-low: #f8f9fa;
        --md-surface-container: #e9ecef;
        --md-surface-container-high: #dee2e6;
        --md-surface-container-highest: #ced4da;
        --md-on-surface: #1a1c1e; /* Dark Charcoal text */
        --md-on-surface-variant: #495057;
        --md-outline: #79747e;
        --md-outline-variant: #e0e0e0; /* Soft borders */
        --md-secondary: #5c6370;
        --md-secondary-container: #f1f3f5;
        --md-tertiary: #bb8009;
        --md-tertiary-container: #fef3c7;
        --md-error: #ba1a1a;
        --md-error-container: #ffdad6;
        --md-on-error: #ffffff;
        --md-on-error-container: #410002;
        --md-green: #1a8754;
        --md-green-bg: #d1e7dd;
        --md-red: #dc3545;
        --md-red-bg: #f8d7da;
        --md-amber: #b58105;
        --md-amber-bg: #fff3cd;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 18px;
        --radius-xl: 24px;
        --radius-full: 9999px;
        --shadow-card: 0 4px 12px rgba(0, 0, 0, 0.05);
        --shadow-elevated: 0 12px 24px rgba(0, 0, 0, 0.08);
        --font-family: 'Inter', sans-serif;
    }

    /* Mượt mà hiệu ứng cuộn trang */
    html {
        scroll-behavior: smooth;
    }

    html, body, #root, .stApp {
        font-family: var(--font-family) !important;
        background-color: var(--md-surface) !important;
        color: var(--md-on-surface) !important;
    }

    /* Animation cho Card */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(15px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-family) !important;
        color: var(--md-on-surface) !important;
    }
    h1 {
        font-size: 32px !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.2 !important;
        background: linear-gradient(135deg, #0f4c81 30%, #1a5f96 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    h2 { font-size: 22px !important; font-weight: 700 !important; line-height: 1.3 !important; }
    h3 { font-size: 18px !important; font-weight: 600 !important; line-height: 1.4 !important; }

    section[data-testid="stSidebar"] {
        background-color: #f1f3f5 !important;
        border-right: 1px solid var(--md-outline-variant) !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        font-size: 14px !important;
        color: var(--md-on-surface-variant) !important;
    }

    /* Premium Button */
    .stButton > button {
        font-family: var(--font-family) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        border: 1px solid var(--md-outline-variant) !important;
        background-color: #ffffff !important;
        color: var(--md-on-surface) !important;
        box-shadow: var(--shadow-card) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        border-color: var(--md-primary) !important;
        box-shadow: var(--shadow-elevated) !important;
        color: var(--md-primary) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--md-primary), #1a5f96) !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1a5f96, #2a7fbe) !important;
        color: #ffffff !important;
    }

    /* Inputs & Selectboxes */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input, .stNumberInput input {
        font-family: var(--font-family) !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--md-outline-variant) !important;
        background-color: #ffffff !important;
        color: var(--md-on-surface) !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus, .stDateInput input:focus, .stNumberInput input:focus {
        border-color: var(--md-primary) !important;
        box-shadow: 0 0 0 2px rgba(15, 76, 129, 0.2) !important;
    }
    
    /* Labels */
    .stSelectbox label, .stTextInput label, .stDateInput label, .stNumberInput label, .stRadio label, .stMultiSelect label, .stSlider label {
        font-family: var(--font-family) !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: var(--md-on-surface) !important;
    }

    /* Custom Glassmorphism Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
        background-color: var(--md-surface-dim) !important;
        padding: 6px !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--md-outline-variant) !important;
        margin-bottom: 20px !important;
    }
    .stTabs button[data-baseweb="tab"] {
        font-family: var(--font-family) !important;
        font-size: 14px !important;
        border-radius: var(--radius-sm) !important;
        padding: 8px 16px !important;
        color: var(--md-on-surface-variant) !important;
        transition: all 0.2s ease !important;
    }
    .stTabs button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
        color: var(--md-primary) !important;
        font-weight: 700 !important;
        box-shadow: var(--shadow-card) !important;
    }

    /* Premium Light Mode Card */
    .md-card {
        background: #ffffff !important;
        border: 1px solid var(--md-outline-variant) !important;
        border-radius: var(--radius-lg) !important;
        padding: 24px !important;
        box-shadow: var(--shadow-card) !important;
        margin-bottom: 16px !important;
        animation: fadeInUp 0.4s ease-out forwards;
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease !important;
    }
    .md-card:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(15, 76, 129, 0.3) !important;
        box-shadow: var(--shadow-elevated) !important;
    }

    .md-chip {
        display: inline-flex !important;
        align-items: center !important;
        padding: 4px 12px !important;
        border-radius: var(--radius-full) !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }
    .md-chip-primary {
        background-color: var(--md-primary-container) !important;
        color: var(--md-primary) !important;
        border: 1px solid rgba(15, 76, 129, 0.2) !important;
    }
    .md-chip-green {
        background-color: var(--md-green-bg) !important;
        color: var(--md-green) !important;
        border: 1px solid rgba(26, 135, 84, 0.2) !important;
    }
    .md-chip-red {
        background-color: var(--md-red-bg) !important;
        color: var(--md-red) !important;
        border: 1px solid rgba(220, 53, 69, 0.2) !important;
    }
    .md-chip-amber {
        background-color: var(--md-amber-bg) !important;
        color: var(--md-amber) !important;
        border: 1px solid rgba(181, 129, 5, 0.2) !important;
    }
    
    /* Destruction Button Styling */
    .stButton button[aria-label*="Xóa"],
    .stButton button[aria-label*="xóa"],
    .stButton button[aria-label*="Xoá"],
    .stButton button[aria-label*="xoá"] {
        background-color: var(--md-red-bg) !important;
        color: var(--md-red) !important;
        border: 1px solid rgba(220, 53, 69, 0.4) !important;
    }
    .stButton button[aria-label*="Xóa"]:hover,
    .stButton button[aria-label*="Xoá"]:hover {
        background-color: var(--md-red) !important;
        color: #ffffff !important;
    }

    .md-status-bar {
        background: #ffffff !important;
        border: 1px solid var(--md-outline-variant) !important;
        border-radius: var(--radius-lg) !important;
        padding: 20px 24px !important;
        box-shadow: var(--shadow-card) !important;
        margin-bottom: 24px;
        animation: fadeInUp 0.3s ease-out;
    }
    .md-section-label {
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: var(--md-on-surface-variant) !important;
    }

    /* Page Navigation styling */
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
        padding: 12px 16px !important;
        border-radius: var(--radius-md) !important;
        text-decoration: none !important;
        font-size: 15px !important;
        font-family: var(--font-family) !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        background-color: transparent !important;
        border: none !important;
        width: 100% !important;
        box-sizing: border-box !important;
        color: var(--md-on-surface-variant) !important;
    }
    [data-testid="stPageLink"] > a:hover {
        background-color: var(--md-surface-dim) !important;
        color: var(--md-primary) !important;
        transform: translateX(3px) !important;
    }
    [data-testid="stPageLink"] > a[aria-current="page"] {
        background-color: var(--md-primary-container) !important;
        color: var(--md-primary) !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow-card) !important;
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

    /* --- MOBILE RESPONSIVENESS OVERRIDES --- */
    @media (max-width: 768px) {
        h1 {
            font-size: 24px !important;
        }
        h2 {
            font-size: 18px !important;
        }
        .md-card {
            padding: 16px !important;
            margin-bottom: 12px !important;
        }
        .md-status-bar {
            padding: 16px !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 16px !important;
        }
        .md-status-bar > div {
            width: 100% !important;
        }
        /* Mobile Touch Target 48px */
        .stButton > button {
            width: 100% !important;
            height: 48px !important;
            font-size: 16px !important;
        }
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input, .stNumberInput input {
            height: 48px !important;
            font-size: 16px !important;
        }
    }
</style>
""", unsafe_allow_html=True)


def render_sidebar(active_page="home"):
    # 1. Hide default navigation
    st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)
    
    # 2. Inject global fonts, Material symbols, design system, responsive styles
    inject_premium_css()

    # 3. Render HTML sidebar
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
            <div style="font-weight: 700; font-size: 16px; color: #ffffff; line-height: 1.2;">Quản lý T04</div>
            <div style="font-size: 11px; color: var(--md-on-surface-variant); letter-spacing: 0.03em;">Hệ thống định mức</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        st.page_link("app.py", label="Trang chủ", icon=":material/home:")
        st.page_link("pages/1_Dashboard.py", label="Bảng điều khiển", icon=":material/dashboard:")
        st.page_link("pages/2_QuanLyCanBo.py", label="Quản lý Cán bộ", icon=":material/groups:")
        st.page_link("pages/3_NhatKyHoatDong.py", label="Nhật ký Hoạt động", icon=":material/edit_note:")
        st.page_link("pages/5_NhapDuLieu.py", label="Nhập dữ liệu Excel", icon=":material/download:")
        st.page_link("pages/4_CaiDatHeThong.py", label="Cài đặt Hệ thống", icon=":material/settings:")

        st.markdown("""
<div style="
    margin-top: 32px;
    padding: 16px;
    background-color: var(--md-surface-container-low);
    border: 1px solid var(--md-outline-variant);
    border-radius: var(--radius-md);
    font-size: 12px;
    color: var(--md-on-surface-variant);
    line-height: 1.5;
    display: flex;
    align-items: start;
    gap: 8px;
">
    <span class="material-symbols-outlined" style="font-size: 16px; margin-top: 1px;">info</span>
    <div>v2.0 — Hệ thống định mức T04</div>
</div>
""", unsafe_allow_html=True)

def render_step_header(step_num, title, description=None):
    desc_html = f'<div style="color: var(--md-on-surface-variant); font-size: 0.9rem; margin-top: 4px;">{description}</div>' if description else ""
    st.markdown(f"""
    <div style="margin-top: 24px; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="
                background-color: var(--md-primary); 
                color: #ffffff; 
                font-weight: 700; 
                width: 24px; 
                height: 24px; 
                border-radius: 50%; 
                display: inline-flex; 
                align-items: center; 
                justify-content: center;
                font-size: 0.85rem;
            ">{step_num}</span>
            <span style="font-weight: 700; font-size: 1.1rem; color: var(--md-on-surface);">{title}</span>
        </div>
        {desc_html}
    </div>
    """, unsafe_allow_html=True)

def render_error_report(errors):
    errors_html = "".join([f'<li style="margin-bottom: 6px;">{err}</li>' for err in errors])
    st.markdown(f"""
    <div style="
        background-color: #fdf2f2;
        border: 1px solid #f5c2c2;
        border-radius: var(--radius-md);
        padding: 16px 20px;
        color: #9b1c1c;
        margin: 16px 0;
        font-size: 0.95rem;
    ">
        <div style="font-weight: 700; display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span class="material-symbols-outlined" style="font-size: 20px; color: #df1b1b;">error</span>
            Phát hiện lỗi dữ liệu ({len(errors)} lỗi):
        </div>
        <ul style="margin: 0; padding-left: 20px;">
            {errors_html}
        </ul>
    </div>
    """, unsafe_allow_html=True)

def render_success_preview(df):
    st.markdown(f"""
    <div style="
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: var(--radius-md);
        padding: 16px 20px;
        color: #166534;
        margin: 16px 0;
        font-size: 0.95rem;
    ">
        <div style="font-weight: 700; display: flex; align-items: center; gap: 8px;">
            <span class="material-symbols-outlined" style="font-size: 20px; color: #15803d;">check_circle</span>
            File hợp lệ! Sẵn sàng nhập {len(df)} cán bộ.
        </div>
    </div>
    """, unsafe_allow_html=True)
