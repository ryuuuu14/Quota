import streamlit as st
import os

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DB_PATH', os.path.join(_project_root, 'data', 'database.sqlite'))

from database import init_db, seed_initial_data, get_connection
from components import render_sidebar

# Auto-initialize on every startup (CREATE IF NOT EXISTS is idempotent)
init_db()

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

render_sidebar("home")

# ── Welcome page ──
st.title("Hệ thống Quản lý Chế độ Làm việc T04")
st.markdown("""
<div style="color: var(--md-on-surface-variant); font-size: 16px; line-height: 1.6; margin-bottom: 24px;">
Chào mừng đến với hệ thống quản lý định mức giờ chuẩn và nghiên cứu khoa học.
</div>

<h3 style="margin-top: 32px;">Hướng dẫn sử dụng:</h3>
<ol style="color: var(--md-on-surface-variant); font-size: 16px; line-height: 1.8; padding-left: 20px;">
    <li><strong>Cài đặt Hệ thống:</strong> Cấu hình các thông số cơ bản (Năm học, Quy tắc miễn giảm, Hoạt động, v.v.).</li>
    <li><strong>Quản lý Cán bộ:</strong> Thêm hồ sơ nhà giáo và ghi nhận diễn biến công tác (chức danh, đơn vị, miễn giảm).</li>
    <li><strong>Nhật ký Hoạt động:</strong> Nhập liệu các hoạt động giảng dạy, NCKH, coi thi, chấm thi, v.v.</li>
    <li><strong>Dashboard:</strong> Theo dõi tiến độ hoàn thành, định mức và thực hiện quy đổi giờ theo Điều 12 (nếu đủ điều kiện).</li>
</ol>
<p style="color: var(--md-on-surface-variant); font-size: 16px; margin-top: 16px;">
    <em>Vui lòng chọn chức năng trên thanh menu bên trái để tiếp tục.</em>
</p>
""", unsafe_allow_html=True)

# ── Regulation Viewer ──
with st.expander("📄 Xem Quy định chế độ làm việc T04 (Toàn văn)", expanded=False):
    reg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md")
    if os.path.exists(reg_path):
        with open(reg_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.warning("Không tìm thấy file quy định chế độ làm việc.")
