import streamlit as st
import pandas as pd
from datetime import date
from database import get_connection
from components import render_empty_state, render_warning_state, render_sidebar

st.set_page_config(page_title="Ghi nhận Hoạt động", page_icon="📝", layout="wide")
render_sidebar("nhatky")

st.title("📝 Ghi nhận Hoạt động")
st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 16px;">Nhập liệu các hoạt động giảng dạy, NCKH và nhiệm vụ khác.</p>', unsafe_allow_html=True)

conn = get_connection()

df_teachers = pd.read_sql_query("SELECT id, name, subject_group FROM teachers", conn)
df_activities = pd.read_sql_query("SELECT * FROM activity_types", conn)
df_timeframes = pd.read_sql_query("SELECT id, name, start_date, end_date FROM timeframes ORDER BY id DESC", conn)

if df_teachers.empty or df_activities.empty or df_timeframes.empty:
    render_warning_state("Cần thêm Nhà giáo, cấu hình Loại hoạt động và Năm học trước khi ghi nhận nhật ký.")
    conn.close()
else:
    teacher_options = {f"{row['name']} ({row['subject_group']})": int(row['id']) for idx, row in df_teachers.iterrows()}
    tf_options = {row['name']: int(row['id']) for idx, row in df_timeframes.iterrows()}

    tab_list, tab_new = st.tabs(["📋 Lịch sử Hoạt động (Gần đây)", "➕ Ghi nhận mới"])

    with tab_list:
        query = """
        SELECT al.id, t.name as 'Nhà giáo', at.name as 'Hoạt động', tf.name as 'Timeframe',
               al.log_date as 'Ngày', al.quantity as 'Số lượng', al.class_level as 'Cấp/Lớp',
               al.class_type, al.student_count as 'Sĩ số', al.note as 'Ghi chú',
               at.category, at.base_conversion_rate, at.is_teaching_activity, at.is_nckh_activity,
               al.timeframe_id
        FROM activity_logs al
        JOIN teachers t ON al.teacher_id = t.id
        JOIN activity_types at ON al.activity_type_id = at.id
        JOIN timeframes tf ON al.timeframe_id = tf.id
        ORDER BY al.log_date DESC, al.id DESC
        LIMIT 100
        """
        
        from calculations import calculate_activity_hours
        df_logs = pd.read_sql_query(query, conn)
        
        if not df_logs.empty:
            hours_list = []
            for idx, row in df_logs.iterrows():
                hours = calculate_activity_hours(
                    row.rename({'Số lượng': 'quantity', 'Cấp/Lớp': 'class_level', 'Sĩ số': 'student_count'}),
                    row
                )
                hours_list.append(hours)
            df_logs['Giờ chuẩn (Ước tính)'] = hours_list
    
            display_cols = [
                'id', 'Nhà giáo', 'Hoạt động', 'Ngày', 'Số lượng',
                'Cấp/Lớp', 'Sĩ số', 'Giờ chuẩn (Ước tính)', 'Ghi chú'
            ]
            df_display = df_logs[[c for c in display_cols if c in df_logs.columns]]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
            st.markdown("### 🗑️ Xoá Nhật ký")
            del_id = st.selectbox(
                "Chọn dòng nhật ký cần xoá:", 
                options=df_logs['id'].tolist(),
                format_func=lambda x: f"Dòng #{x}: {df_logs[df_logs['id'] == x]['Nhà giáo'].values[0]} - {df_logs[df_logs['id'] == x]['Hoạt động'].values[0]} ({df_logs[df_logs['id'] == x]['Timeframe'].values[0]})"
            )
            
            selected_log_row = df_logs[df_logs['id'] == del_id].iloc[0]
            log_tf_id = int(selected_log_row['timeframe_id'])
            
            # Check if timeframe is locked by Excel data
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM session_teacher_totals WHERE timeframe_id = ?", (log_tf_id,))
            log_tf_locked = cursor.fetchone()[0] > 0
            
            if log_tf_locked:
                st.warning("⚠️ Không thể xoá dòng nhật ký này vì năm học tương ứng đã được khóa để quản lý qua Excel.")
            else:
                confirm_key = f"confirm_del_log_{del_id}"
                if st.session_state.get(confirm_key, False):
                    st.warning(f"⚠️ Bạn có chắc chắn muốn xóa dòng nhật ký #{del_id} này không?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Xác nhận xóa vĩnh viễn", key=f"yes_log_{del_id}", type="primary"):
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM activity_logs WHERE id = ?", (int(del_id),))
                            conn.commit()
                            st.session_state[confirm_key] = False
                            st.success("Đã xoá thành công!")
                            st.rerun()
                    with col_no:
                        if st.button("Hủy bỏ", key=f"no_log_{del_id}"):
                            st.session_state[confirm_key] = False
                            st.rerun()
                else:
                    if st.button("🗑️ Yêu cầu xoá dòng này", key=f"req_log_{del_id}"):
                        st.session_state[confirm_key] = True
                        st.rerun()
        else:
            render_empty_state("Chưa có nhật ký hoạt động nào.")

    with tab_new:
        col_left, col_right = st.columns(2)
        teacher_sel = col_left.selectbox("Chọn Nhà giáo", options=list(teacher_options.keys()))

        activity_options = {f"[{row['category']}] {row['name']}": int(row['id']) for idx, row in df_activities.iterrows()}
        activity_sel = col_right.selectbox("Chọn Hoạt động", options=list(activity_options.keys()))
        selected_act_id = activity_options[activity_sel]
        act_info = df_activities[df_activities['id'] == selected_act_id].iloc[0]
        unit = act_info['unit']

        col3, col4 = st.columns(2)
        log_date = col3.date_input("Ngày thực hiện", value=date.today())
        
        matching_tf_name = "Chưa xác định"
        matching_tf_id = None
        log_date_str = log_date.isoformat()
        for idx, row in df_timeframes.iterrows():
            if row['start_date'] <= log_date_str <= row['end_date']:
                matching_tf_id = int(row['id'])
                matching_tf_name = row['name']
                break
        if matching_tf_id is None and not df_timeframes.empty:
            matching_tf_id = int(df_timeframes.iloc[0]['id'])
            matching_tf_name = df_timeframes.iloc[0]['name']

        col4.markdown(f'<div style="padding-top: 10px;"><label style="font-size: 14px; font-weight: 600; color: var(--md-on-surface-variant);">Hệ thống tự động nhận diện Năm học</label><div style="font-size: 16px; font-weight: 700; color: var(--md-primary); margin-top: 8px;">📅 {matching_tf_name}</div></div>', unsafe_allow_html=True)
        
        with st.expander("⚙️ Thay đổi Năm học thủ công (nếu cần)", expanded=False):
            tf_list = list(tf_options.keys())
            default_index = 0
            for idx, (name, tf_id) in enumerate(tf_options.items()):
                if tf_id == matching_tf_id:
                    default_index = idx
                    break
            tf_sel = st.selectbox("Chọn Năm học khác", options=tf_list, index=default_index)
        
        # Xác định timeframe được áp dụng cuối cùng
        final_tf_id = tf_options[tf_sel]
        
        # Check lock state for the selected target timeframe
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM session_teacher_totals WHERE timeframe_id = ?", (final_tf_id,))
        is_tf_locked = cursor.fetchone()[0] > 0
        
        if is_tf_locked:
            st.warning(f"⚠️ Năm học **{tf_sel}** đã được khóa nhập lẻ để quản lý tập trung bằng Excel. Vui lòng chọn năm học khác hoặc xóa file Excel tại trang Nhập dữ liệu để mở khóa.")
            
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

            class_level = "Đại học" if act_info['is_teaching_activity'] and not is_freeform else None
            class_type = "Lý thuyết" if act_info['is_teaching_activity'] and not is_freeform else None
            student_count = 40 if act_info['is_teaching_activity'] and not is_freeform else 0
            nckh_level = None
            is_main_author = False

            if act_info['is_teaching_activity'] and not is_freeform:
                st.info("💡 Hệ thống mặc định hệ số lớp: Đại học, Lý thuyết, 40 SV. Chỉ thay đổi dưới đây nếu cần.")
                with st.expander("📐 Chi tiết Lớp học (để tính hệ số)", expanded=False):
                    col_a_c, col_b_c, col_c_c = st.columns(3)
                    class_level = col_a_c.selectbox("Cấp học", ["Đại học", "Thạc sĩ", "Tiến sĩ", "LLCT Trung cấp", "LLCT Cao cấp", "Bồi dưỡng"], index=0)
                    class_type = col_b_c.selectbox("Loại hình", ["Lý thuyết", "Thực hành", "Ngoại ngữ/CNTT", "Thảo luận", "Bài tập", "Xêmina"], index=0)
                    student_count = col_c_c.number_input("Sĩ số (quyết định hệ số nhân)", min_value=1, max_value=200, value=40)

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
                    nckh_role_options = {
                        "Cấp Quốc gia (Chủ nhiệm / Tác giả chính)": ("Quốc gia", True),
                        "Cấp Quốc gia (Thành viên tham gia)": ("Quốc gia", False),
                        "Cấp Bộ / Tỉnh (Chủ nhiệm / Tác giả chính)": ("Bộ/Tỉnh", True),
                        "Cấp Bộ / Tỉnh (Thành viên tham gia)": ("Bộ/Tỉnh", False),
                        "Cấp Cơ sở (Chủ nhiệm / Tác giả chính)": ("Cơ sở", True),
                        "Cấp Cơ sở (Thành viên tham gia)": ("Cơ sở", False),
                        "Cấp Trường (Chủ nhiệm / Tác giả chính)": ("Trường", True),
                        "Cấp Trường (Thành viên tham gia)": ("Trường", False),
                    }
                    nckh_role_sel = st.selectbox(
                        "Vai trò & Cấp độ đề tài/bài báo",
                        options=list(nckh_role_options.keys())
                    )
                    nckh_level, is_main_author = nckh_role_options[nckh_role_sel]

            if is_freeform:
                note = freeform_desc
            else:
                note = st.text_input("Ghi chú chi tiết")

            submit = st.form_submit_button("Lưu nhật ký", disabled=is_tf_locked)

            if submit and not is_tf_locked:
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
                    0.0, note, final_tf_id
                ))
                conn.commit()
                st.success("Đã lưu nhật ký thành công!")
                st.rerun()

conn.close()
