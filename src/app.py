import streamlit as st
import os
import textwrap

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DB_PATH', os.path.join(_project_root, 'data', 'database.sqlite'))

from database import init_db, seed_initial_data, get_connection
from components import render_sidebar

# Auto-initialize once per session (CREATE IF NOT EXISTS + seeding is idempotent)
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# Auto-seed if DB appears empty (e.g. brand-new data/database.sqlite)
_conn = get_connection()
_tf_count = _conn.execute("SELECT COUNT(*) FROM timeframes").fetchone()[0]
_act_count = _conn.execute("SELECT COUNT(*) FROM activity_types").fetchone()[0]
_red_count = _conn.execute("SELECT COUNT(*) FROM reduction_rules").fetchone()[0]
_conn.close()

if _tf_count == 0:
    seed_initial_data()

if _act_count == 0:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    import seed_activities
    seed_activities.run()

if _red_count == 0:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    import seed_reductions
    seed_reductions.run()

_conn2 = get_connection()
_teacher_count = _conn2.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
_conn2.close()

if _teacher_count < 5:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    import seed_teachers
    seed_teachers.run()


st.set_page_config(
    page_title="Hệ thống Quản lý Chế độ Làm việc T04",
    layout="wide",
    initial_sidebar_state="expanded"
)

from auth import get_current_user
_gate_user = get_current_user()
if not _gate_user:
    st.switch_page("pages/8_DangNhap.py")
    st.stop()

render_sidebar("home")

# ── Welcome page ──
st.markdown("""
<div style="
background: linear-gradient(135deg, rgba(128, 0, 32, 0.08), rgba(0, 103, 71, 0.04));
padding: 32px;
border-radius: var(--radius-lg);
margin-bottom: 32px;
border: 1px solid rgba(255, 255, 255, 0.08);
border-top: 3px solid var(--md-green);
box-shadow: var(--shadow-card);
">
<h2 style="margin: 0 0 12px 0; color: var(--md-on-surface); font-weight: 800;">Hệ thống Quản lý Chế độ Làm việc Nhà giáo T04</h2>
<p style="margin: 0; color: var(--md-on-surface-variant); font-size: 16px; line-height: 1.6;">
Hỗ trợ tự động hóa việc tính toán định mức giờ dạy chuẩn và giờ nghiên cứu khoa học theo Quy định T04. Hệ thống tự động phân bổ định mức theo số ngày làm việc thực tế, tự động áp dụng các quy tắc miễn giảm và hỗ trợ quy đổi bù trừ giữa giờ dạy và giờ nghiên cứu khoa học.
</p>
</div>

<h3 style="margin-bottom: 20px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
<span class="material-symbols-outlined" style="color: var(--md-primary);">explore</span>
Quy trình 4 bước sử dụng hệ thống
</h3>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 32px;">
<!-- Step 1 -->
<div class="md-card" style="display: flex; flex-direction: column; justify-content: space-between; height: 100%; margin-bottom: 0px;">
<div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
<span class="md-chip md-chip-primary" style="font-size: 11px; padding: 4px 10px;">BƯỚC 1</span>
<span class="material-symbols-outlined" style="color: var(--md-primary); font-size: 28px;">settings</span>
</div>
<h4 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 700; color: var(--md-on-surface);">Cài đặt Quy chế & Danh mục</h4>
<p style="margin: 0; font-size: 14px; color: var(--md-on-surface-variant); line-height: 1.5;">
Thiết lập <strong>Năm học/Học kỳ</strong>, quy định số ngày làm việc thực tế, định mức chuẩn cho từng <strong>Chức danh</strong>, và các quy tắc <strong>Miễn giảm</strong>.
</p>
</div>
<div style="margin-top: 16px; font-size: 13px; color: var(--md-primary); font-weight: 600;">
👉 Mục: Cài đặt Hệ thống
</div>
</div>

<!-- Step 2 -->
<div class="md-card" style="display: flex; flex-direction: column; justify-content: space-between; height: 100%; margin-bottom: 0px;">
<div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
<span class="md-chip md-chip-primary" style="font-size: 11px; padding: 4px 10px;">BƯỚC 2</span>
<span class="material-symbols-outlined" style="color: var(--md-primary); font-size: 28px;">groups</span>
</div>
<h4 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 700; color: var(--md-on-surface);">Quản lý Hồ sơ & Timeline</h4>
<p style="margin: 0; font-size: 14px; color: var(--md-on-surface-variant); line-height: 1.5;">
Tạo hồ sơ nhà giáo và cập nhật <strong>Quá trình công tác (Timeline)</strong>. Định mức nghĩa vụ sẽ tự động phân bổ <strong>theo tỷ lệ ngày</strong> khi chức vụ/chức danh thay đổi.
</p>
</div>
<div style="margin-top: 16px; font-size: 13px; color: var(--md-primary); font-weight: 600;">
👉 Mục: Quản lý Cán bộ
</div>
</div>

<!-- Step 3 -->
<div class="md-card" style="display: flex; flex-direction: column; justify-content: space-between; height: 100%; margin-bottom: 0px;">
<div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
<span class="md-chip md-chip-primary" style="font-size: 11px; padding: 4px 10px;">BƯỚC 3</span>
<span class="material-symbols-outlined" style="color: var(--md-primary); font-size: 28px;">edit_note</span>
</div>
<h4 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 700; color: var(--md-on-surface);">Nhập Nhật ký Hoạt động</h4>
<p style="margin: 0; font-size: 14px; color: var(--md-on-surface-variant); line-height: 1.5;">
Ghi nhận các hoạt động thực hiện (Giảng dạy, NCKH, Nghiên cứu chuyên đề, Coi thi/Chấm thi). Hệ thống sẽ tự động nhân với <strong>hệ số quy đổi</strong> chuẩn.
</p>
</div>
<div style="margin-top: 16px; font-size: 13px; color: var(--md-primary); font-weight: 600;">
👉 Mục: Nhật ký Hoạt động
</div>
</div>

<!-- Step 4 -->
<div class="md-card" style="display: flex; flex-direction: column; justify-content: space-between; height: 100%; margin-bottom: 0px;">
<div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
<span class="md-chip md-chip-primary" style="font-size: 11px; padding: 4px 10px;">BƯỚC 4</span>
<span class="material-symbols-outlined" style="color: var(--md-primary); font-size: 28px;">dashboard</span>
</div>
<h4 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 700; color: var(--md-on-surface);">Theo dõi & Quyết toán</h4>
<p style="margin: 0; font-size: 14px; color: var(--md-on-surface-variant); line-height: 1.5;">
Áp dụng quy tắc bù trừ để tự động đối chiếu và chuyển đổi giờ thừa giữa hai nhiệm vụ Giảng dạy và Nghiên cứu khoa học khi đạt điều kiện tối thiểu.
</p>
</div>
<div style="margin-top: 16px; font-size: 13px; color: var(--md-primary); font-weight: 600;">
👉 Mục: Bảng điều khiển
</div>
</div>
</div>

<div style="
background-color: var(--md-surface-container-low);
border: 1px solid var(--md-outline-variant);
border-radius: var(--radius-lg);
padding: 24px;
margin-bottom: 32px;
">
<h4 style="margin: 0 0 12px 0; display: flex; align-items: center; gap: 8px; color: var(--md-on-surface); font-weight: 700;">
<span class="material-symbols-outlined" style="color: var(--md-amber);">lightbulb</span>
Nguyên tắc cốt lõi của Quy định T04:
</h4>
<ul style="margin: 0; padding-left: 20px; color: var(--md-on-surface-variant); font-size: 14px; line-height: 1.6;">
<li style="margin-bottom: 8px;"><strong>Tính toán theo tỷ lệ (Pro-rata):</strong> Khi nhà giáo thay đổi thông tin (ví dụ: được bổ nhiệm chức vụ quản lý giữa năm học, nghỉ thai sản, đi học), định mức giờ chuẩn sẽ được chia nhỏ thành từng giai đoạn và tính tỷ lệ chính xác theo số ngày thực tế.</li>
<li style="margin-bottom: 8px;"><strong>Khấu trừ ngày làm việc đột xuất:</strong> Các ngày nghỉ bệnh, đi công tác dài ngày sẽ trực tiếp làm giảm số ngày làm việc định mức, từ đó giảm trừ tương ứng nghĩa vụ giờ dạy và nghiên cứu khoa học.</li>
<li><strong>Bù trừ nghĩa vụ giảng dạy và nghiên cứu khoa học:</strong> Giờ giảng dạy thừa có thể quy đổi sang giờ nghiên cứu khoa học, và ngược lại giờ nghiên cứu khoa học thừa có thể dùng để bù đắp cho giờ giảng dạy còn thiếu, giúp nhà giáo hoàn thành tổng nghĩa vụ công tác trong năm học.</li>
</ul>
</div>
""", unsafe_allow_html=True)

# ── Regulation Viewer ──
with st.expander("📄 Xem Quy định chế độ làm việc T04 (Toàn văn)", expanded=False):
    reg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md")
    if os.path.exists(reg_path):
        with open(reg_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.warning("Không tìm thấy file quy định chế độ làm việc.")
