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
    color: var(--md-on-surface);
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
<span style="color: var(--md-on-surface); font-size: 2.2rem; font-weight: 800; font-family: var(--font-family); letter-spacing: -0.02em;">{value}</span>{delta_html}
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


_PREMIUM_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,0&display=swap" rel="stylesheet">
<style>
    :root {
        --md-primary: #FFC107; /* Gold — brand accent */
        --md-primary-container: rgba(255, 193, 7, 0.15);
        --md-on-primary: #1A1A1A;
        --md-primary-fixed: rgba(255, 193, 7, 0.10);
        --md-primary-fixed-dim: rgba(255, 193, 7, 0.20);
        --md-surface: #FDF8F3; /* Warm cream — content area */
        --md-surface-dim: #F5F0EB;
        --md-surface-container-lowest: #FFFFFF;
        --md-surface-container-low: #F5F0EB;
        --md-surface-container: #EFE8DD;
        --md-surface-container-high: #E8DED0;
        --md-on-surface: #1A1A1A; /* Near-black on cream */
        --md-on-surface-variant: #5C5248; /* Warm gray */
        --md-outline: #D4C9BC;
        --md-outline-variant: #E8DED0;
        --md-secondary: #4A5D23; /* Military Green */
        --md-secondary-container: rgba(74, 93, 35, 0.15);
        --md-tertiary: #C9A84C; /* Gold */
        --md-tertiary-container: rgba(201, 168, 76, 0.15);
        --md-error: #DC2626;
        --md-error-container: rgba(220, 38, 38, 0.10);
        --md-green: #4A5D23;
        --md-green-bg: rgba(74, 93, 35, 0.12);
        --md-red: #DC2626;
        --md-red-bg: rgba(220, 38, 38, 0.10);
        --md-amber: #FFC107;
        --md-amber-bg: rgba(255, 193, 7, 0.12);
        --md-burgundy: #800020;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 18px;
        --radius-xl: 24px;
        --radius-full: 9999px;
        --shadow-card: 0 4px 16px rgba(0, 0, 0, 0.08);
        --shadow-elevated: 0 12px 32px rgba(0, 0, 0, 0.12);
        --font-family: 'Be Vietnam Pro', sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }

    /* Mượt mà hiệu ứng cuộn trang */
    html {
        scroll-behavior: smooth;
    }

    /* Focus indicators for keyboard nav */
    *:focus-visible {
        outline: 2px solid var(--md-primary) !important;
        outline-offset: 2px !important;
        border-radius: var(--radius-sm) !important;
    }
    button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
        outline: 2px solid var(--md-primary) !important;
        outline-offset: 2px !important;
    }
    .stButton > button:focus-visible {
        outline: 2px solid var(--md-primary) !important;
        outline-offset: 2px !important;
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
        color: var(--md-primary) !important;
    }
    h2 { font-size: 22px !important; font-weight: 700 !important; line-height: 1.3 !important; }
    h3 { font-size: 18px !important; font-weight: 600 !important; line-height: 1.4 !important; }

    /* Custom Glassmorphism Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: transparent !important;
        padding: 0px !important;
        border-radius: 0px !important;
        border: none !important;
        margin-bottom: 24px !important;
    }
    .stTabs button[data-baseweb="tab"] {
        font-family: var(--font-family) !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        background-color: var(--md-surface-dim) !important;
        border-radius: var(--radius-md) !important;
        padding: 10px 24px !important;
        border: 1px solid var(--md-outline-variant) !important;
        color: var(--md-on-surface-variant) !important;
        transition: all 0.2s ease !important;
    }
    .stTabs button[data-baseweb="tab"]:hover {
        border-color: var(--md-primary) !important;
        color: var(--md-primary) !important;
    }
    .stTabs button[data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--md-primary-container) !important;
        color: var(--md-primary) !important;
        border-color: var(--md-primary-container) !important;
        box-shadow: var(--shadow-card) !important;
        font-weight: 700 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #800020 !important; /* Burgundy chrome */
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] .md-section-label,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        color: rgba(255, 255, 255, 0.85) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] > a {
        color: rgba(255, 255, 255, 0.70) !important;
        background-color: transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] > a:hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #FFC107 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] > a[aria-current="page"] {
        background-color: rgba(255, 193, 7, 0.15) !important;
        color: #FFC107 !important;
        border-left: 4px solid #FFC107 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] > a[aria-current="page"] p {
        color: #FFC107 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] span {
        color: inherit !important;
    }
    /* Premium Button */
    .stButton > button {
        font-family: var(--font-family) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
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
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: var(--md-primary) !important;
        color: var(--md-on-primary) !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background: #E5A800 !important;
        color: var(--md-on-primary) !important;
        box-shadow: var(--shadow-elevated) !important;
    }

    /* Data tables: monospace for numbers */
    .stDataFrame {
        border: 1px solid var(--md-outline-variant) !important;
        border-radius: var(--radius-md) !important;
        overflow: hidden !important;
    }
    .stDataFrame th {
        background-color: var(--md-surface-dim) !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: var(--md-on-surface-variant) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        padding: 10px 12px !important;
    }
    .stDataFrame td {
        font-size: 13px !important;
        font-variant-numeric: tabular-nums !important;
        padding: 8px 12px !important;
    }
    .stDataFrame tr:nth-child(even) td {
        background-color: var(--md-surface-container-lowest) !important;
    }

    /* MultiSelect */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--md-outline-variant) !important;
    }

    /* Slider */
    .stSlider div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--md-primary) !important;
    }

    /* TextArea */
    .stTextArea textarea {
        font-family: var(--font-family) !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--md-outline-variant) !important;
        background-color: #FFFFFF !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--md-primary) !important;
    }

    /* Sidebar logout button */
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.10) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.18) !important;
        color: #FFFFFF !important;
        transform: none !important;
        box-shadow: none !important;
    }
    /* Remove Streamlit's slide/underline indicator on sidebar button */
    section[data-testid="stSidebar"] .stButton > button::after,
    section[data-testid="stSidebar"] .stButton > button::before {
        display: none !important;
        border: none !important;
        background: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button p {
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
    }
    .stSelectbox input:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Labels */
    .stSelectbox label, .stTextInput label, .stDateInput label, .stNumberInput label, .stRadio label, .stMultiSelect label, .stSlider label {
        font-family: var(--font-family) !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: var(--md-on-surface) !important;
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
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .md-card:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(255, 193, 7, 0.3) !important;
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
        background-color: var(--md-primary) !important;
        color: var(--md-on-primary) !important;
        border: none !important;
    }
    .md-chip-green {
        background-color: var(--md-green) !important;
        color: #ffffff !important;
        border: none !important;
    }
    .md-chip-red {
        background-color: var(--md-error) !important;
        color: #ffffff !important;
        border: none !important;
    }
    .md-chip-amber {
        background-color: var(--md-amber) !important;
        color: var(--md-on-primary) !important;
        border: none !important;
    }
    .md-chip-tertiary {
        background-color: var(--md-tertiary-container) !important;
        color: var(--md-tertiary) !important;
        border: 1px solid rgba(201, 168, 76, 0.3) !important;
    }
    
    /* Destruction Button Styling */
    .stButton button[aria-label*="Xóa"],
    .stButton button[aria-label*="xóa"],
    .stButton button[aria-label*="Xoá"],
    .stButton button[aria-label*="xoá"] {
        background-color: var(--md-red-bg) !important;
        color: var(--md-red) !important;
        border: 1px solid rgba(220, 38, 38, 0.4) !important;
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
        background-color: var(--md-surface-container) !important;
        color: var(--md-primary) !important;
        transform: translateX(3px) !important;
    }
    [data-testid="stPageLink"] > a[aria-current="page"] {
        background-color: var(--md-primary-container) !important;
        color: var(--md-primary) !important;
        font-weight: 700 !important;
        border-left: 4px solid var(--md-primary) !important;
        border-radius: 0 8px 8px 0 !important;
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

    /* === CONTAINED EXPANDERS: prevent full-width sprawl === */
    div[data-testid="stExpander"] {
        max-width: 820px !important;
        border: 1px solid var(--md-outline-variant) !important;
        border-radius: var(--radius-lg) !important;
        background: #ffffff !important;
        box-shadow: var(--shadow-card) !important;
        margin-bottom: 20px !important;
        overflow: hidden !important;
        transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
    }
    div[data-testid="stExpander"]:hover {
        border-color: rgba(255, 193, 7, 0.25) !important;
        box-shadow: var(--shadow-elevated) !important;
    }
    /* Expander header row */
    div[data-testid="stExpander"] > div:first-child {
        padding: 14px 20px !important;
        background: var(--md-surface-container) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        border-bottom: 1px solid var(--md-outline-variant) !important;
        cursor: pointer !important;
        transition: background 0.15s ease !important;
        user-select: none !important;
    }
    div[data-testid="stExpander"] > div:first-child:hover {
        background: var(--md-surface-container-high) !important;
    }
    /* Expander content area */
    div[data-testid="stExpander"] > div:nth-child(2) {
        padding: 20px 24px !important;
    }
    /* Nested expanders: reduce size but keep constraint */
    div[data-testid="stExpander"] div[data-testid="stExpander"] {
        max-width: 100% !important;
        margin-bottom: 12px !important;
        border-radius: var(--radius-md) !important;
    }
    div[data-testid="stExpander"] div[data-testid="stExpander"] > div:first-child {
        padding: 10px 16px !important;
        font-size: 13px !important;
    }
    div[data-testid="stExpander"] div[data-testid="stExpander"] > div:nth-child(2) {
        padding: 16px !important;
    }
    /* Expander inside side-columns (columns) — let it fill */
    div[data-testid="column"] div[data-testid="stExpander"] {
        max-width: 100% !important;
    }

    /* === CONTENT AREA RESCALE: prevent edge-to-edge sprawl === */
    .main .block-container {
        max-width: 1320px !important;
        padding-left: 28px !important;
        padding-right: 28px !important;
    }
    /* Full-width data tables within the constrained container */
    .stDataFrame {
        max-width: 100% !important;
    }
    /* Big metric cards row — let it breathe */
    div[data-testid="column"] {
        padding: 0 6px !important;
    }

    /* === FORM ELEMENTS INSIDE EXPANDERS: better proportions === */
    div[data-testid="stExpander"] .stTextInput,
    div[data-testid="stExpander"] .stSelectbox,
    div[data-testid="stExpander"] .stDateInput,
    div[data-testid="stExpander"] .stNumberInput {
        max-width: 480px !important;
    }
    div[data-testid="stExpander"] .row-widget.stRadio {
        max-width: 640px !important;
    }

    /* === BETTER GLOBAL SPACING === */
    hr {
        margin: 20px 0 !important;
        opacity: 0.5 !important;
    }
    .stForm {
        max-width: 720px !important;
    }

    /* === PILL-BUTTON RADIO GROUPS (horizontal) === */
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] {
        display: flex;
        flex-direction: row;
        gap: 4px;
        flex-wrap: wrap;
        background: var(--md-surface-container-low);
        padding: 4px;
        border-radius: var(--radius-full);
        border: 1px solid var(--md-outline-variant);
        width: fit-content;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label {
        display: inline-flex !important;
        align-items: center;
        justify-content: center;
        padding: 5px 18px !important;
        min-height: 34px;
        border-radius: var(--radius-full) !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        font-size: 13px;
        font-weight: 500;
        color: var(--md-on-surface-variant);
        margin: 0 !important;
        flex: 0 1 auto;
        white-space: nowrap;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label:hover {
        background: var(--md-surface-container-high) !important;
        color: var(--md-on-surface);
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label:has(input:checked) {
        background: var(--md-primary) !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(255, 193, 7, 0.30);
    }
    div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label > div:first-child {
        display: none !important;
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
"""

def inject_premium_css():
    st.markdown(_PREMIUM_CSS, unsafe_allow_html=True)





@st.cache_data(ttl=30)
def _get_pending_batch_count():
    try:
        from database import get_connection
        _c = get_connection().cursor()
        _c.execute("SELECT COUNT(*) FROM import_batches WHERE status = 'pending'")
        return _c.fetchone()[0]
    except Exception:
        return 0

@st.cache_data(ttl=60)
def _get_sidebar_system_stats():
    _db_ok = False
    _tf_name = "—"
    _teacher_count = 0
    _guest_count = 0
    _has_excel = False
    try:
        from database import get_connection
        _conn_sidebar = get_connection()
        _c = _conn_sidebar.cursor()
        _c.execute("SELECT COUNT(*) FROM teachers WHERE employment_type IN ('TEACHER','STAFF')")
        _teacher_count = _c.fetchone()[0]
        _c.execute("SELECT COUNT(*) FROM teachers WHERE employment_type = 'GUEST'")
        _guest_count = _c.fetchone()[0]
        _c.execute("SELECT name FROM timeframes ORDER BY start_date DESC LIMIT 1")
        _r = _c.fetchone()
        if _r: _tf_name = _r[0]
        _c.execute("SELECT COUNT(*) FROM session_teacher_totals")
        _has_excel = _c.fetchone()[0] > 0
        _conn_sidebar.close()
        _db_ok = True
    except Exception:
        _db_ok = False
    return _db_ok, _tf_name, _teacher_count, _guest_count, _has_excel


def render_sidebar(active_page="home"):
    # Build system status data (cached)
    _db_ok, _tf_name, _teacher_count, _guest_count, _has_excel = _get_sidebar_system_stats()
    _pending_batches = _get_pending_batch_count()

    _dot_color = "#22c55e" if _db_ok else "#ef4444"
    _dot_label = "Đã kết nối" if _db_ok else "Mất kết nối"
    _source_icon = "download" if _has_excel else "edit_note"
    _source_label = "Excel" if _has_excel else "Nhập lẻ"

    # Render HTML sidebar
    with st.sidebar:
        # Inject CSS (inside sidebar so it persists across page navigation)
        st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)
        inject_premium_css()

        from auth import get_current_user
        user = get_current_user()
        
        if user:
            role_labels = {
                "admin": "Quản trị viên",
                "head_dept": f"Trưởng {user.get('department_name') or 'Khoa'}"
            }
            role_label = role_labels.get(user["role"], "Người dùng")
            identity_html = (
                f'<div style="margin-top: 12px; padding: 10px 12px; background: rgba(255,255,255,0.06); border-radius: var(--radius-md); border: 1px solid rgba(255,255,255,0.12);">'
                f'  <div style="font-size: 11px; color: rgba(255,255,255,0.60); font-weight: 500;">Tài khoản hoạt động:</div>'
                f'  <div style="font-weight: 700; color: #FFC107; font-size: 14px; margin-top: 2px;">{user["username"]}</div>'
                f'  <div style="font-size: 10px; color: rgba(255,255,255,0.50); margin-top: 1px; font-weight: 600; text-transform: uppercase;">{role_label}</div>'
                f'</div>'
            )
        else:
            identity_html = (
                '<div style="margin-top: 12px; padding: 10px 12px; background: rgba(239,68,68,0.05); border-radius: var(--radius-md); border: 1px solid rgba(239,68,68,0.15);">'
                '  <div style="font-size: 11px; color: #f87171; font-weight: 600; text-transform: uppercase; display: flex; align-items: center; gap: 4px;">'
                '    <span class="material-symbols-outlined" style="font-size: 14px;">lock</span> Chế độ Khách (Đọc)'
                '  </div>'
                '</div>'
            )

        st.markdown(f"""
<div style="padding: 8px 16px 24px 16px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="
            width: 40px; height: 40px;
            background: linear-gradient(135deg, rgba(255,193,7,0.20), #FFC107);
            border-radius: var(--radius-md);
            display: flex; align-items: center; justify-content: center;
            color: #1A1A1A;
            font-size: 20px;
        ">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">school</span>
        </div>
        <div>
            <div style="font-weight: 700; font-size: 16px; color: #FFFFFF; line-height: 1.2;">Quản lý T04</div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.55); letter-spacing: 0.03em;">Hệ thống định mức</div>
        </div>
    </div>
    {identity_html}
</div>
""", unsafe_allow_html=True)

        st.page_link("app.py", label="Trang chủ", icon=":material/home:")
        st.page_link("pages/1_Dashboard.py", label="Bảng điều khiển", icon=":material/dashboard:")
        st.page_link("pages/2_QuanLyCanBo.py", label="Quản lý Cán bộ", icon=":material/groups:")
        st.page_link("pages/3_NhatKyHoatDong.py", label="Nhật ký Hoạt động", icon=":material/edit_note:")
        
        # Role-based menu links
        role = user["role"] if user else None
        if role in ["admin", "head_dept"]:
            st.page_link("pages/4_CaiDatHeThong.py", label="Cài đặt Hệ thống", icon=":material/settings:")
        if role == "admin":
            st.page_link("pages/6_Payroll.py", label="Quản lý Lương TT11", icon=":material/payments:")
            if _pending_batches:
                _pc1, _pc2 = st.columns([1, 0.12])
                with _pc1:
                    st.page_link("pages/7_PheDuyet.py", label="Phê duyệt Dữ liệu", icon=":material/fact_check:", use_container_width=True)
                with _pc2:
                    st.markdown(f"<div style='background:#ef4444;color:white;font-size:11px;font-weight:700;min-width:20px;height:20px;border-radius:999px;display:flex;align-items:center;justify-content:center;padding:0 4px;'>{_pending_batches}</div>", unsafe_allow_html=True)
            else:
                st.page_link("pages/7_PheDuyet.py", label="Phê duyệt Dữ liệu", icon=":material/fact_check:")
            
        login_label = "Thông tin tài khoản" if user else "Đăng nhập"
        st.page_link("pages/8_DangNhap.py", label=login_label, icon=":material/lock:")

        if user:
            from auth import logout
            if st.button("Đăng xuất", type="primary", use_container_width=True):
                logout()
                st.switch_page("pages/8_DangNhap.py")

        st.markdown('<div style="margin-top:24px;border-top:1px solid rgba(255,255,255,0.08);padding-top:12px;"></div>', unsafe_allow_html=True)
        st.page_link("pages/5_DesignSystem.py", label="Design System", icon=":material/palette:")

        # System status bar
        st.markdown(f"""
<div style="
    margin-top: 32px;
    padding: 12px 14px;
    background-color: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: var(--radius-md);
    font-size: 11px;
    color: rgba(255,255,255,0.60);
    line-height: 1.6;
">
    <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.08); font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em; color: rgba(255,255,255,0.50);">
        <span class="material-symbols-outlined" style="font-size: 14px;">monitor_heart</span>
        Trạng thái hệ thống
    </div>
    <div style="display: grid; grid-template-columns: auto 1fr; gap: 4px 8px;">
        <span style="color: rgba(255,255,255,0.50);">CSDL</span>
        <div style="display: flex; align-items: center; gap: 4px; color: rgba(255,255,255,0.70);">
            <span style="width: 6px; height: 6px; border-radius: 50%; background-color: {_dot_color}; display: inline-block;"></span>
            <span>{_dot_label}</span>
        </div>
        <span style="color: rgba(255,255,255,0.50);">Năm học</span>
        <span style="font-weight: 500; color: rgba(255,255,255,0.80);">{_tf_name}</span>
        <span style="color: rgba(255,255,255,0.50);">CB-CV</span>
        <span style="font-weight: 500; color: rgba(255,255,255,0.80);">{_teacher_count} cơ hữu + {_guest_count} khách mời</span>
        <span style="color: rgba(255,255,255,0.50);">Nguồn số liệu</span>
        <div style="display: flex; align-items: center; gap: 4px; color: rgba(255,255,255,0.70);">
            <span class="material-symbols-outlined" style="font-size: 12px;">{_source_icon}</span>
            <span style="font-weight: 500;">{_source_label}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

def render_step_header(step_num, title, description=None):
    desc_html = f'<div style="color: var(--md-on-surface-variant); font-size: 0.9rem; margin-top: 4px;">{description}</div>' if description else ""
    st.markdown(f"""
    <div style="margin-top: 24px; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="
                background-color: var(--md-primary); 
                color: var(--md-on-primary); 
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
        background-color: var(--md-error-container);
        border: 1px solid var(--md-error);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        color: var(--md-error);
        margin: 16px 0;
        font-size: 0.95rem;
    ">
        <div style="font-weight: 700; display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span class="material-symbols-outlined" style="font-size: 20px; color: var(--md-error);">error</span>
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
        background-color: var(--md-green-bg);
        border: 1px solid var(--md-green);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        color: var(--md-green);
        margin: 16px 0;
        font-size: 0.95rem;
    ">
        <div style="font-weight: 700; display: flex; align-items: center; gap: 8px;">
            <span class="material-symbols-outlined" style="font-size: 20px; color: var(--md-green);">check_circle</span>
            File hợp lệ! Sẵn sàng nhập {len(df)} cán bộ.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_diff_viewer(
    staging_df,
    diff_json_str: str,
    domain: str,
    batch_id: int,
    view_mode: str = "inline",
    key_prefix: str = "diff"
):
    """
    Render a diff comparison view using AgGrid with cell-level highlighting,
    with a fallback to st.dataframe.

    Parameters
    ----------
    staging_df : pd.DataFrame
        Staging rows for this batch.
    diff_json_str : str
        JSON string from import_batches.diff_json.
    domain : str
        One of VALID_DOMAINS.
    batch_id : int
        For unique AgGrid key generation.
    view_mode : str
        "inline" or "side_by_side".
    key_prefix : str
        For session state isolation.
    """
    try:
        from pipeline.diff_formatter import format_diff_json
    except ImportError:
        _render_fallback_diff(staging_df, domain)
        return

    formatted_df = format_diff_json(diff_json_str, domain, staging_df)
    if formatted_df.empty:
        st.info("Không có dữ liệu để hiển thị.")
        return

    # Build summary chips
    markers = formatted_df["_diff_marker"].value_counts()
    st.markdown(f"""
    <div style="display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;">
        <span class="md-chip md-chip-green">🆕 Mới: {markers.get('NEW', 0)}</span>
        <span class="md-chip md-chip-amber">🟡 Cập nhật: {markers.get('UPDATE', 0)}</span>
        <span class="md-chip md-chip-red">🔴 Xóa: {markers.get('DELETE', 0)}</span>
        <span class="md-chip">⚪ Bỏ qua: {markers.get('SKIP', 0)}</span>
    </div>
    """, unsafe_allow_html=True)

    # Display columns (exclude internal ones)
    display_cols = [c for c in formatted_df.columns
                    if not c.startswith("_")]
    try:
        _render_aggrid_diff(formatted_df, display_cols, batch_id, view_mode, key_prefix)
    except Exception:
        _render_fallback_diff(staging_df, domain)


def _render_aggrid_diff(formatted_df, display_cols, batch_id, view_mode, key_prefix):
    """Render diff using streamlit-aggrid with cell-level styles."""
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

    display_df = formatted_df[display_cols].copy()

    # Build column definitions with cell style renderers
    gb = GridOptionsBuilder.from_dataframe(display_df)

    # Cell style JS — colors cells based on _cell_styles metadata
    cell_style_js = JsCode("""
    function(params) {
        if (!params.data || !params.data._cell_styles) return {};
        const styles = JSON.parse(params.data._cell_styles || '{}');
        const col = params.colDef ? params.colDef.field : '';
        if (!col) return {};
        const cellClass = styles[col];
        if (cellClass === 'added') {
            return {'backgroundColor': '#d1fae5', 'color': '#065f46'};
        } else if (cellClass === 'removed') {
            return {'backgroundColor': '#ffe4e6', 'color': '#9f1239'};
        } else if (cellClass === 'changed') {
            return {'backgroundColor': '#fef3c7', 'color': '#92400e'};
        }
        return {};
    }
    """)

    for col in display_df.columns:
        gb.configure_column(
            col,
            cellStyle=cell_style_js,
            wrapText=False,
            autoHeight=False
        )

    # Add diff marker column with status chip
    if "_diff_marker_display" in formatted_df.columns:
        gb.configure_column(
            "_diff_marker_display",
            headerName="Trạng thái",
            width=140,
            pinned="left"
        )

    gb.configure_grid_options(
        domLayout="normal",
        rowHeight=32,
        headerHeight=38,
        suppressColumnVirtualisation=False,
        enableCellTextSelection=True,
        ensureDomOrder=True,
    )

    gb.configure_selection(
        selection_mode="multiple",
        use_checkbox=False
    )

    grid_options = gb.build()

    ag_grid_key = f"{key_prefix}_aggrid_{batch_id}_{view_mode}"

    grid_response = AgGrid(
        display_df,
        gridOptions=grid_options,
        height=min(600, 40 * len(display_df) + 80),
        key=ag_grid_key,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        reload_data=False,
        fit_columns_on_grid_load=True,
        theme="streamlit",
    )


def _render_fallback_diff(staging_df, domain):
    """Fallback renderer using native st.dataframe when AgGrid is unavailable."""
    config_map = {
        "teachers": {"cols": ["row_num", "teacher_name", "department", "title", "diff_marker", "diff_detail"],
                     "rename": {"row_num": "Dòng", "teacher_name": "Họ tên", "department": "Đơn vị",
                                "title": "Chức danh", "diff_marker": "Trạng thái", "diff_detail": "Chi tiết"}},
        "activities": {"cols": ["row_num", "teacher_name", "activity_type_name", "diff_marker", "diff_detail"],
                       "rename": {"row_num": "Dòng", "teacher_name": "Mã GV", "activity_type_name": "Hoạt động",
                                  "diff_marker": "Trạng thái", "diff_detail": "Chi tiết"}},
        "schedule": {"cols": ["row_num", "teacher_name", "subject_name", "diff_marker", "diff_detail"],
                     "rename": {"row_num": "Dòng", "teacher_name": "Họ tên", "subject_name": "Môn",
                                "diff_marker": "Trạng thái", "diff_detail": "Chi tiết"}},
        "aggregate_totals": {"cols": ["row_num", "teacher_name", "diff_marker", "diff_detail"],
                             "rename": {"row_num": "Dòng", "teacher_name": "Mã GV",
                                        "diff_marker": "Trạng thái", "diff_detail": "Chi tiết"}}
    }
    config = config_map.get(domain, config_map["teachers"])
    available = [c for c in config["cols"] if c in staging_df.columns]
    display = staging_df[available].rename(columns=config["rename"])
    st.dataframe(display, use_container_width=True, hide_index=True)
