import os

file_path = r'f:\annd\Quota\src\pages\2_QuanLyCanBo.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find breakpoints
idx_import = -1
idx_manual = -1
idx_fetch = -1

for i, line in enumerate(lines):
    if '# --- TOP: NHẬP HÀNG LOẠT ---' in line:
        idx_import = i
    elif '# --- TOP: THÊM MỚI HỒ SƠ ---' in line:
        idx_manual = i
    elif '# --- FETCH TEACHERS ---' in line:
        idx_fetch = i

print(f"import: {idx_import}, manual: {idx_manual}, fetch: {idx_fetch}")

header = lines[:idx_import]
import_block = lines[idx_import:idx_manual]
manual_block = lines[idx_manual:idx_fetch]
fetch_block = lines[idx_fetch:]

css_and_tabs = """
# --- GLOBAL CSS INJECTION & TABS ---
st.markdown('''
<style>
/* Sophisticated Architectural Layout */
[data-testid="stTabs"] { background: transparent; }
[data-testid="stTabs"] button {
    font-family: 'Inter', 'Roboto', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px;
    padding: 0;
    margin-bottom: 24px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background-color: var(--md-surface-container-low);
    border-radius: 8px;
    padding: 10px 24px;
    border: 1px solid var(--md-outline-variant);
    color: var(--md-on-surface);
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    background-color: #1e293b; /* Midnight blue */
    color: #f8fafc !important; /* High contrast text */
    border: 1px solid #0f172a;
}
.sp-card {
    background: var(--md-surface-container);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid var(--md-outline-variant);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}
.badge {
    padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;
}
.badge.new { background: #22c55e; color: white; }
.badge.update { background: #eab308; color: black; }
.badge.skip { background: #94a3b8; color: white; }
</style>
''', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "📋 Danh sách & Tìm kiếm",
    "➕ Cập nhật hồ sơ",
    "📥 Nhập dữ liệu từ Excel"
])

"""

new_lines = header + [css_and_tabs]

new_lines.append("with tab1:\n")
# Indent fetch block
for line in fetch_block:
    if line.strip() == "":
        new_lines.append("\n")
    else:
        new_lines.append("    " + line)

new_lines.append("\nwith tab2:\n")
# Indent manual block
for line in manual_block:
    if line.strip() == "":
        new_lines.append("\n")
    else:
        new_lines.append("    " + line)

new_lines.append("\nwith tab3:\n")
# Indent import block
for line in import_block:
    if line.strip() == "":
        new_lines.append("\n")
    else:
        new_lines.append("    " + line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Successfully refactored 2_QuanLyCanBo.py into 3 tabs.")
