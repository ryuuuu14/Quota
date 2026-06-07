import streamlit as st
import pandas as pd
import sqlite3
import io
import time
from database import get_connection
from components import render_sidebar, render_metric_card, render_chip
from payroll import run_payroll_cycle, get_payroll_records

st.set_page_config(page_title="Quản lý Chế độ chi TT11", layout="wide")
render_sidebar("payroll")

from auth import require_role
if not require_role(["admin"], page_title="Quản lý Chế độ chi TT11"):
    st.stop()

st.title("Quản lý Chế độ chi Giáo dục, Đào tạo (TT11/2026)")
st.markdown(
    '<p style="color: var(--md-on-surface-variant); font-size: 14px;">'
    "Tính lương cơ bản, thù lao khách mời & vượt giờ theo Thông tư 11/2026/TT-BCA. "
    "Chạy lại sẽ xoá dữ liệu lương cũ của kỳ học đó.</p>",
    unsafe_allow_html=True,
)

def get_timeframes():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, name FROM timeframes ORDER BY start_date DESC", conn)
    conn.close()
    return dict(zip(df['name'], df['id']))

def get_teacher_stats(tf_id):
    conn = get_connection()
    cur = conn.cursor()
    total_ts = cur.execute("SELECT COUNT(*) FROM teachers WHERE employment_type IN ('TEACHER','STAFF')").fetchone()[0]
    has_salary = cur.execute("SELECT COUNT(*) FROM teachers WHERE employment_type IN ('TEACHER','STAFF') AND (total_12m_salary > 0 OR salary_coefficient > 0)").fetchone()[0]
    missing_salary = total_ts - has_salary
    guest_count = cur.execute("SELECT COUNT(*) FROM teachers WHERE employment_type = 'GUEST'").fetchone()[0]
    log_count = cur.execute("SELECT COUNT(*) FROM activity_logs WHERE timeframe_id = ?", (tf_id,)).fetchone()[0]
    conn.close()
    return {
        "total_ts": total_ts,
        "has_salary": has_salary,
        "missing_salary": missing_salary,
        "guest_count": guest_count,
        "log_count": log_count,
    }

def get_teachers_missing_salary():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT name, employment_type FROM teachers "
        "WHERE employment_type IN ('TEACHER', 'STAFF') AND (total_12m_salary IS NULL OR total_12m_salary = 0) AND (salary_coefficient IS NULL OR salary_coefficient = 0)",
        conn,
    )
    conn.close()
    return df

def get_all_teachers():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, name, employment_type, subject_group FROM teachers ORDER BY name", conn
    )
    conn.close()
    return df

timeframes = get_timeframes()
if not timeframes:
    st.warning("Chưa có kỳ học nào trong hệ thống. Vui lòng thêm kỳ học trước.")
    st.stop()

tf_name = st.selectbox("Chọn kỳ học", list(timeframes.keys()), key='tf_main')
tf_id = timeframes[tf_name]

stats = get_teacher_stats(tf_id)
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    render_metric_card("Tổng CB", stats["total_ts"], icon="badge")
with c2:
    render_metric_card("Có lương", stats["has_salary"], icon="payments")
with c3:
    delta = f"+{stats['missing_salary']}" if stats["missing_salary"] > 0 else None
    render_metric_card("Thiếu lương", stats["missing_salary"], delta=delta, icon="warning")
with c4:
    render_metric_card("Khách mời", stats["guest_count"], icon="person")
with c5:
    render_metric_card("Nhật ký", stats["log_count"], icon="edit_note")

missing_salary_df = get_teachers_missing_salary()
if not missing_salary_df.empty:
    with st.expander(f"⚠️ {len(missing_salary_df)} cán bộ thiếu tổng lương 12 tháng", expanded=False):
        st.dataframe(missing_salary_df, hide_index=True, use_container_width=True)
        st.markdown(
            'Vào **Quản lý Cán bộ** → chọn từng cán bộ → **Cập nhật Thông tin cơ bản** → chọn Cấp bậc hàm hoặc nhập Hệ số lương.',
            unsafe_allow_html=True,
        )

st.markdown("---")

df_teachers = get_all_teachers()
teacher_options = {
    f"{row['name']} ({row['employment_type']})": row['id']
    for _, row in df_teachers.iterrows()
}
col_run_left, col_run_right = st.columns([3, 1])
with col_run_left:
    selected_teachers = st.multiselect(
        "Chọn cán bộ cần tính lương (để trống = tính tất cả)",
        options=list(teacher_options.keys()),
    )
with col_run_right:
    n_selected = len(selected_teachers) if selected_teachers else stats["total_ts"] + stats["guest_count"]
    total_avail = stats["total_ts"] + stats["guest_count"]
    st.markdown(
        f'<div style="padding-top: 28px; text-align: right;">'
        f'{render_chip(f"Đã chọn {n_selected}/{total_avail}", "primary", "checklist")}'
        f'</div>',
        unsafe_allow_html=True,
    )

selected_ids = [teacher_options[t] for t in selected_teachers] if selected_teachers else None

c_run, c_spacer = st.columns([1, 3])
with c_run:
    run_disabled = stats["total_ts"] == 0 and stats["guest_count"] == 0
    if st.button("🚀 Chạy bảng lương", type="primary", use_container_width=True, disabled=run_disabled):
        with st.spinner("Đang tính toán lương và thù lao..."):
            result = run_payroll_cycle(tf_id, teacher_ids=selected_ids)
            time.sleep(0.3)
        if "error" in result:
            st.error(f"Lỗi khi tính lương: {result['error']}")
        elif result["guest_count"] == 0 and result["base_count"] == 0 and result["overtime_count"] == 0:
            st.error(f"Không có dữ liệu lương nào được tạo cho {tf_name}")
            with st.expander("Chi tiết nguyên nhân & cách khắc phục", expanded=True):
                if result["details"]:
                    for msg in result["details"]:
                        st.markdown(f"- {msg}")
                st.markdown("---")
                st.markdown("**Hướng dẫn kiểm tra từng bước:**")
                for t, d in [
                    ("Nhật ký hoạt động", "Vào **Ghi nhận Hoạt động** → kiểm tra đã có dữ liệu cho kỳ này?"),
                    ("Tổng lương 12 tháng", "Vào **Quản lý Cán bộ** → Cập nhật → nhập Tổng tiền lương 12 tháng."),
                    ("Chức danh/Chức vụ", "Vào **Quản lý Cán bộ** → đảm bảo có Chức danh giảng dạy và Chức vụ (nếu có)."),
                    ("Định mức GC", "Vào **Dashboard** → nếu Định mức GC=0 → thiếu thông tin chức danh hoặc chức vụ."),
                    ("Khách mời", "Vào **Quản lý Cán bộ** → đảm bảo khách mời có Cấp bậc và nhật ký giảng dạy."),
                ]:
                    st.markdown(f"**{t}:** {d}")
        else:
            guest_info = f"🎓 {result['guest_count']}" if result["guest_count"] > 0 else "0"
            base_info = f"💰 {result['base_count']}" if result["base_count"] > 0 else "0"
            ot_info = f"⏰ {result['overtime_count']}" if result["overtime_count"] > 0 else "0"
            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                render_metric_card("Lương CB", base_info, icon="payments")
            with rc2:
                render_metric_card("Vượt giờ", ot_info, icon="timer")
            with rc3:
                render_metric_card("Khách mời", guest_info, icon="person")
            with rc4:
                render_metric_card("Tổng tiền", f"{result['total_vnd']:,.0f}", icon="account_balance")
            skipped_parts = []
            if result["skipped_no_salary"] > 0:
                skipped_parts.append(f"{result['skipped_no_salary']} thiếu lương")
            if result["skipped_zero_norm"] > 0:
                skipped_parts.append(f"{result['skipped_zero_norm']} không có định mức")
            if result["skipped_no_overtime"] > 0:
                skipped_parts.append(f"{result['skipped_no_overtime']} không vượt giờ")
            if result["guest_no_activities"] > 0:
                skipped_parts.append(f"{result['guest_no_activities']} khách mời không có nhật ký")
            if skipped_parts:
                st.info(f"📌 Bỏ qua: {', '.join(skipped_parts)}")
        st.rerun()

st.markdown("---")
st.markdown("### Kết quả bảng lương")

df_payroll = get_payroll_records(tf_id)

if df_payroll.empty:
    st.info("Chưa có dữ liệu lương cho kỳ học này. Chạy bảng lương để tạo dữ liệu.")
else:
    df_payroll['amount_vnd_str'] = df_payroll['amount_vnd'].apply(lambda x: f"{x:,.0f} VNĐ")

    col_f1, col_f2, col_tot = st.columns([2, 2, 1])
    with col_f1:
        emp_types = ["Tất cả"] + sorted(df_payroll['employment_type'].unique().tolist())
        emp_filter = st.selectbox("Loại nhân sự", emp_types, key="emp_filter")
    with col_f2:
        task_types = ["Tất cả"] + sorted(df_payroll['task_type'].unique().tolist())
        task_filter = st.selectbox("Loại công việc", task_types, key="task_filter")

    filtered = df_payroll.copy()
    if emp_filter != "Tất cả":
        filtered = filtered[filtered['employment_type'] == emp_filter]
    if task_filter != "Tất cả":
        filtered = filtered[filtered['task_type'] == task_filter]

    total_filtered = filtered['amount_vnd'].sum()

    with col_tot:
        st.markdown(
            f'<div style="padding-top: 28px; text-align: right;">'
            f'<span style="font-size: 1.3rem; font-weight: 800; color: var(--md-primary);">'
            f'{total_filtered:,.0f} VNĐ</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.dataframe(
        filtered[
            ['teacher_name', 'employment_type', 'guest_rank', 'task_type', 'quantity', 'amount_vnd_str', 'log_date']
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "teacher_name": "Tên nhân sự",
            "employment_type": "Loại",
            "guest_rank": "Cấp bậc khách mời",
            "task_type": "Loại công việc",
            "quantity": "Số lượng/Giờ",
            "amount_vnd_str": "Thành tiền",
            "log_date": "Ngày tính",
        },
    )

    col_ex, col_cl, _ = st.columns([1, 1, 4])
    with col_ex:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            filtered.to_excel(writer, index=False, sheet_name='Bảng lương')
        st.download_button(
            "📥 Xuất Excel",
            data=buf.getvalue(),
            file_name=f"bang_luong_{tf_name.replace(' ','_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col_cl:
        clear_key = f"clear_{tf_id}"
        if st.session_state.get(clear_key, False):
            st.warning("Xác nhận xóa toàn bộ dữ liệu lương cho kỳ học này?")
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("Xác nhận xóa", key=f"confirm_{tf_id}", type="primary"):
                    conn = get_connection()
                    conn.execute("DELETE FROM payroll_records WHERE timeframe_id = ?", (tf_id,))
                    conn.commit()
                    conn.close()
                    st.session_state[clear_key] = False
                    st.success("Đã xóa dữ liệu bảng lương.")
                    st.rerun()
            with cc2:
                if st.button("Hủy", key=f"cancel_{tf_id}"):
                    st.session_state[clear_key] = False
                    st.rerun()
        else:
            if st.button("🗑️ Xóa dữ liệu kỳ này", use_container_width=True):
                st.session_state[clear_key] = True
                st.rerun()
