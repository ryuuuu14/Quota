import streamlit as st
import pandas as pd
from datetime import date
from database import get_connection
from components import render_empty_state, render_warning_state, render_sidebar

render_sidebar("nhatky")

st.title("Ghi nhận Hoạt động")
st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 16px;">Nhập liệu các hoạt động giảng dạy, NCKH và nhiệm vụ khác.</p>', unsafe_allow_html=True)

conn = get_connection()

df_teachers = pd.read_sql_query("SELECT id, name FROM teachers", conn)
df_activities = pd.read_sql_query("SELECT * FROM activity_types", conn)
df_timeframes = pd.read_sql_query("SELECT id, name FROM timeframes ORDER BY id DESC", conn)

if df_teachers.empty or df_activities.empty or df_timeframes.empty:
    render_warning_state("Cần thêm Nhà giáo, cấu hình Loại hoạt động và Timeframe trước khi ghi nhận nhật ký.")
else:
    teacher_options = {f"{row['name']} (ID: {row['id']})": int(row['id']) for idx, row in df_teachers.iterrows()}
    tf_options = {row['name']: int(row['id']) for idx, row in df_timeframes.iterrows()}

    with st.expander("Ghi nhận mới", expanded=True):
        col_t, col_c, col_a = st.columns(3)
        teacher_sel = col_t.selectbox("Chọn Nhà giáo", options=list(teacher_options.keys()))

        categories = sorted(df_activities['category'].unique())
        category_sel = col_c.selectbox("Danh mục hoạt động", options=categories)

        filtered_activities = df_activities[df_activities['category'] == category_sel]
        activity_options = {row['name']: row['id'] for idx, row in filtered_activities.iterrows()}
        activity_sel = col_a.selectbox("Hoạt động cụ thể", options=list(activity_options.keys()))

        col3, col4 = st.columns(2)
        log_date = col3.date_input("Ngày thực hiện", value=date.today())
        tf_sel = col4.selectbox("Thuộc Năm học", options=list(tf_options.keys()))

        selected_act_id = activity_options[activity_sel]
        act_info = df_activities[df_activities['id'] == selected_act_id].iloc[0]
        unit = act_info['unit']

        with st.form("log_activity_form"):
            is_freeform = (act_info['category'] == 'Chấp hành Nhiệm vụ khác')

            if is_freeform:
                freeform_desc = st.text_area("Mô tả nhiệm vụ", placeholder="Ví dụ: Tham gia hội thảo an ninh, họp chuyên môn đột xuất,...")
                total_hours = st.number_input("Tổng số giờ thực hiện", min_value=0.0, value=1.0, step=0.5,
                                              help="Nhập trực tiếp tổng số giờ đã thực hiện (không qua quy đổi)")
                st.info("Hoạt động này không tính vào giờ chuẩn giảng dạy (GC) — chỉ mang tính thống kê.")
                quantity = total_hours
            else:
                quantity = st.number_input(f"Số lượng gốc ({unit})", min_value=0.0, value=1.0, step=0.5)

            class_level = None
            class_type = None
            student_count = 0
            nckh_level = None
            is_main_author = False

            if act_info['is_teaching_activity'] and not is_freeform:
                st.markdown("""
<div style="
    background-color: var(--md-primary-fixed);
    padding: 8px 16px;
    border-radius: var(--radius-md);
    border-left: 4px solid var(--md-primary-container);
    color: var(--md-on-primary-fixed);
    font-weight: 700;
    font-size: 0.9rem;
    margin: 16px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
">
    <span class="material-symbols-outlined" style="font-size: 20px;">school</span>
    Chi tiết Giảng dạy (Làm cơ sở nhân hệ số chuẩn)
</div>
                """, unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns(3)
                class_level = col_a.selectbox("Cấp học", ["Đại học", "Thạc sĩ", "Tiến sĩ", "LLCT Trung cấp", "LLCT Cao cấp", "Bồi dưỡng"])
                class_type = col_b.selectbox("Loại hình", ["Lý thuyết", "Thực hành", "Ngoại ngữ/CNTT", "Thảo luận", "Bài tập", "Xêmina"])
                student_count = col_c.number_input("Sĩ số (quyết định hệ số nhân)", min_value=1, max_value=200, value=40)

            elif act_info['is_nckh_activity']:
                st.markdown("""
<div style="
    background-color: var(--md-green-bg);
    padding: 8px 16px;
    border-radius: var(--radius-md);
    border-left: 4px solid var(--md-green);
    color: var(--md-green);
    font-weight: 700;
    font-size: 0.9rem;
    margin: 16px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
">
    <span class="material-symbols-outlined" style="font-size: 20px;">biotech</span>
    Chi tiết NCKH
</div>
                """, unsafe_allow_html=True)
                if act_info['category'] == 'NCKH - Hướng dẫn thi đấu':
                    rate = act_info['base_conversion_rate']
                    st.info(f"Hoạt động này được tính cố định **{rate}h** chuẩn NCKH theo quy định.")
                else:
                    col_a, col_b = st.columns(2)
                    nckh_level = col_a.selectbox("Cấp độ", ["Quốc gia", "Bộ/Tỉnh", "Cơ sở", "Trường"])
                    is_main_author = col_b.checkbox("Là tác giả chính/Chủ nhiệm", value=True)

            if is_freeform:
                note = freeform_desc
            else:
                note = st.text_input("Ghi chú chi tiết")

            submit = st.form_submit_button("Lưu nhật ký")

            if submit:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO activity_logs (
                        teacher_id, activity_type_id, log_date, quantity,
                        class_level, class_type, student_count, nckh_level, is_main_author,
                        converted_hours, note, timeframe_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    teacher_options[teacher_sel], selected_act_id, log_date, quantity,
                    class_level, class_type, student_count, nckh_level, int(is_main_author),
                    0.0, note, tf_options[tf_sel]
                ))
                conn.commit()
                st.success("Đã lưu nhật ký thành công!")
                st.rerun()

    st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 24px 0;">', unsafe_allow_html=True)
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">history</span> Lịch sử Hoạt động (Gần đây)</h3>', unsafe_allow_html=True)

    query = """
    SELECT al.id, t.name as 'Nhà giáo', at.name as 'Hoạt động', tf.name as 'Timeframe',
           al.log_date as 'Ngày', al.quantity as 'Số lượng', al.class_level as 'Cấp/Lớp',
           al.student_count as 'Sĩ số', al.note as 'Ghi chú'
    FROM activity_logs al
    JOIN teachers t ON al.teacher_id = t.id
    JOIN activity_types at ON al.activity_type_id = at.id
    JOIN timeframes tf ON al.timeframe_id = tf.id
    ORDER BY al.log_date DESC, al.id DESC
    LIMIT 100
    """
    df_logs = pd.read_sql_query(query, conn)
    if not df_logs.empty:
        st.dataframe(df_logs, width='stretch', hide_index=True)

        with st.expander("Xoá Nhật ký"):
            del_id = int(st.selectbox("Chọn ID nhật ký cần xoá", options=df_logs['id'].tolist()))
            if st.button("Xoá log này", type="primary"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM activity_logs WHERE id = ?", (del_id,))
                conn.commit()
                st.success("Đã xoá thành công!")
                st.rerun()
    else:
        render_empty_state("Chưa có nhật ký hoạt động nào.")

conn.close()
