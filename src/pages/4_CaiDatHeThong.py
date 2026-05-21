import streamlit as st
import pandas as pd
from database import get_connection
from components import render_empty_state, render_sidebar

render_sidebar("caidat")

st.title("Cài đặt Thông số Hệ thống")
st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 16px;">Cấu hình toàn diện các danh mục: năm học, đơn vị, chức danh, chức vụ, miễn giảm và hoạt động.</p>', unsafe_allow_html=True)

conn = get_connection()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Năm học", "Đơn vị", "Chức danh", "Chức vụ", "Miễn giảm", "Hoạt động"
])

def render_delete_button(table, row_id, id_col='id'):
    confirm_key = f"confirm_{table}_{row_id}"
    if st.session_state.get(confirm_key, False):
        st.markdown('<span style="color: var(--md-red); font-size: 13px; font-weight:600;">Xóa?</span>', unsafe_allow_html=True)
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Có", key=f"yes_{table}_{row_id}"):
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM {table} WHERE {id_col} = ?", (int(row_id) if id_col == 'id' else row_id,))
                    conn.commit()
                    st.session_state[confirm_key] = False
                    st.success("Đã xoá!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")
        with col_no:
            if st.button("Hủy", key=f"no_{table}_{row_id}"):
                st.session_state[confirm_key] = False
                st.rerun()
    else:
        if st.button("Xóa", key=f"del_{table}_{row_id}"):
            st.session_state[confirm_key] = True
            st.rerun()

def render_list_item(content, del_table=None, del_id=None, del_col='id', badge_html=None):
    badge = f'<span style="margin-left: 8px;">{badge_html}</span>' if badge_html else ""
    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown(f"""
<div style="
    background-color: var(--md-surface-container-lowest);
    padding: 16px 20px;
    border-radius: var(--radius-md);
    border: 1px solid var(--md-outline-variant);
    margin-bottom: 8px;
    box-shadow: var(--shadow-card);
    display: flex;
    align-items: center;
    justify-content: space-between;
">
    <div>{content}{badge}</div>
</div>
        """, unsafe_allow_html=True)
    with col2:
        if del_table and del_id is not None:
            render_delete_button(del_table, del_id, del_col)

with tab1:
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">calendar_month</span> Quản lý Năm học / Học kỳ</h3>', unsafe_allow_html=True)

    df_tf = pd.read_sql_query("SELECT id, name, start_date, end_date FROM timeframes", conn)
    if df_tf.empty:
        render_empty_state("Chưa có năm học nào.")
    else:
        for _, row in df_tf.iterrows():
            content = f'<span style="color: var(--md-on-surface); font-weight: 600;">{row["name"]}</span><span style="color: var(--md-on-surface-variant); font-size: 0.85rem; margin-left: 8px;">({row["start_date"]} đến {row["end_date"]})</span>'
            render_list_item(content, 'timeframes', row['id'])

    with st.expander("Thêm Năm học mới"):
        with st.form("add_tf_form"):
            tf_name = st.text_input("Tên Năm học")
            tf_start = st.date_input("Ngày bắt đầu")
            tf_end = st.date_input("Ngày kết thúc")

            if st.form_submit_button("Thêm"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO timeframes (name, start_date, end_date) VALUES (?, ?, ?)",
                                   (tf_name, tf_start, tf_end))
                    conn.commit()
                    st.success("Thêm thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 24px 0;">', unsafe_allow_html=True)
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">edit_calendar</span> Điều chỉnh ngày làm việc đột xuất</h3>', unsafe_allow_html=True)
    st.markdown("""
<p style="color: var(--md-on-surface-variant); font-size: 14px;">
Ghi nhận các thay đổi bất thường trong năm học: nghỉ bù, nghỉ do bão lũ,
đóng cửa đột xuất làm giảm ngày làm việc thực tế. Các ngày nghỉ chuẩn
(Tết Nguyên đán, 2/9, 30/4+1/5, nghỉ hè) đã được tính sẵn trong khung
thời gian năm học và không cần nhập tại đây.
</p>
    """, unsafe_allow_html=True)

    df_holidays = pd.read_sql_query("""
        SELECT h.id, h.name, h.start_date, h.end_date, t.name as timeframe_name
        FROM academic_holidays h
        JOIN timeframes t ON h.timeframe_id = t.id
    """, conn)

    if df_holidays.empty:
        render_empty_state("Chưa có điều chỉnh nào. Các ngày nghỉ chuẩn (Tết, 2/9, hè) đã được tính sẵn trong khung thời gian.")
    else:
        for _, row in df_holidays.iterrows():
            days_count = (pd.to_datetime(row['end_date']) - pd.to_datetime(row['start_date'])).days + 1
            badge_html = f'<span class="md-chip md-chip-amber"><span class="material-symbols-outlined" style="font-size: 14px; margin-right: 4px;">block</span>{days_count} ngày bị loại</span>'
            col1, col2 = st.columns([8, 2])
            with col1:
                st.markdown(f"""
<div style="
    background-color: var(--md-amber-bg);
    padding: 16px 20px;
    border-radius: var(--radius-md);
    border: 1px solid #fde68a;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
">
    <div>
        <div style="color: var(--md-amber); font-weight: 600;">{row['name']}</div>
        <div style="color: var(--md-on-surface-variant); font-size: 0.85rem; margin-top: 4px;">
            {row['start_date']} → {row['end_date']} | Năm học: <b>{row['timeframe_name']}</b>
        </div>
    </div>
    {badge_html}
</div>
                """, unsafe_allow_html=True)
            with col2:
                render_delete_button('academic_holidays', row['id'])

    with st.expander("Thêm đợt điều chỉnh mới"):
        with st.form("add_holiday_form"):
            h_name = st.text_input("Lý do điều chỉnh (VD: Nghỉ bù sau Tết, Đóng cửa do bão)")

            df_tf_opts = pd.read_sql_query("SELECT id, name FROM timeframes", conn)
            if not df_tf_opts.empty:
                tf_options = {int(row['id']): row['name'] for _, row in df_tf_opts.iterrows()}
                h_tf_id = st.selectbox("Áp dụng cho năm học", options=list(tf_options.keys()), format_func=lambda x: tf_options[x])

                col_date1, col_date2 = st.columns(2)
                h_start = col_date1.date_input("Ngày bắt đầu nghỉ")
                h_end = col_date2.date_input("Ngày kết thúc nghỉ")

                if st.form_submit_button("Thêm điều chỉnh"):
                    if h_start > h_end:
                        st.error("Ngày bắt đầu không được lớn hơn ngày kết thúc!")
                    else:
                        try:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO academic_holidays (timeframe_id, name, start_date, end_date) VALUES (?, ?, ?, ?)",
                                           (h_tf_id, h_name, h_start, h_end))
                            conn.commit()
                            st.success("Đã thêm điều chỉnh. Số tuần làm việc sẽ được tính lại tương ứng.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")
            else:
                st.warning("Vui lòng thêm Năm học trước khi tạo điều chỉnh.")
                st.form_submit_button("Thêm điều chỉnh", disabled=True)

with tab2:
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">business</span> Quản lý Đơn vị</h3>', unsafe_allow_html=True)

    df_depts = pd.read_sql_query("SELECT * FROM departments", conn)
    if df_depts.empty:
        render_empty_state("Chưa có đơn vị nào.")
    else:
        for _, row in df_depts.iterrows():
            type_str = "Có giảng dạy" if row['is_teaching_dept'] else "Hành chính"
            badge_html = f'<span class="md-chip md-chip-{"green" if row["is_teaching_dept"] else "primary"}">{type_str}</span>'
            col1, col2 = st.columns([8, 2])
            with col1:
                st.markdown(f"""
<div style="
    background-color: var(--md-surface-container-lowest);
    padding: 16px 20px;
    border-radius: var(--radius-md);
    border: 1px solid var(--md-outline-variant);
    margin-bottom: 8px;
    box-shadow: var(--shadow-card);
    display: flex;
    align-items: center;
    justify-content: space-between;
">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="color: var(--md-on-surface); font-weight: 600;">{row['name']}</span>
        {badge_html}
    </div>
</div>
                """, unsafe_allow_html=True)
            with col2:
                render_delete_button('departments', row['name'], id_col='name')

    with st.expander("Thêm Đơn vị mới"):
        with st.form("add_dept_form"):
            dept_name = st.text_input("Tên Đơn vị")
            is_teaching = st.checkbox("Là đơn vị có giảng dạy (Khoa, Bộ môn)", value=True)

            if st.form_submit_button("Thêm"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO departments (name, is_teaching_dept) VALUES (?, ?)",
                                   (dept_name, int(is_teaching)))
                    conn.commit()
                    st.success("Thêm thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

with tab3:
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">badge</span> Định mức Cơ bản theo Chức danh</h3>', unsafe_allow_html=True)

    df_titles = pd.read_sql_query("SELECT * FROM titles", conn)
    if df_titles.empty:
        render_empty_state("Chưa có chức danh nào.")
    else:
        for _, row in df_titles.iterrows():
            content = f"""
<div>
    <div style="color: var(--md-on-surface); font-weight: 600;">{row['name']}</div>
    <div style="color: var(--md-on-surface-variant); font-size: 0.85rem; margin-top: 4px;">
        Định mức Giờ giảng (Tự nhiên): <b>{row['base_teaching_hours_natural']}</b> |
        Định mức Giờ giảng (Xã hội): <b>{row['base_teaching_hours_social']}</b> |
        Định mức Giờ NCKH: <b>{row['base_nckh_hours']}</b>
    </div>
</div>
            """
            render_list_item(content, 'titles', row['name'], del_col='name')

    with st.expander("Thêm Chức danh mới"):
        with st.form("add_title_form"):
            t_name = st.text_input("Tên Chức danh")
            col1, col2, col3 = st.columns(3)
            t_nat = col1.number_input("Định mức Giờ giảng - Khối Tự nhiên", min_value=0, step=10, help="Định mức giờ giảng dạy chuẩn hàng năm đối với các môn khoa học Tự nhiên.")
            t_soc = col2.number_input("Định mức Giờ giảng - Khối Xã hội", min_value=0, step=10, help="Định mức giờ giảng dạy chuẩn hàng năm đối với các môn khoa học Xã hội.")
            t_nckh = col3.number_input("Định mức Giờ NCKH", min_value=0, step=10, help="Định mức giờ nghiên cứu khoa học chuẩn hàng năm.")

            if st.form_submit_button("Thêm"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO titles (name, base_teaching_hours_natural, base_teaching_hours_social, base_nckh_hours) VALUES (?, ?, ?, ?)",
                                   (t_name, t_nat, t_soc, t_nckh))
                    conn.commit()
                    st.success("Thêm thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

with tab4:
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">manage_accounts</span> Quy tắc Giảm định mức: Chức vụ Quản lý</h3>', unsafe_allow_html=True)

    df_roles = pd.read_sql_query("SELECT * FROM reduction_rules WHERE rule_type = 'ROLE'", conn)
    if df_roles.empty:
        render_empty_state("Chưa có chức vụ nào.")
    else:
        for _, row in df_roles.iterrows():
            content = f"""
<div>
    <div style="color: var(--md-on-surface); font-weight: 600;">{row['name']}</div>
    <div style="color: var(--md-on-surface-variant); font-size: 0.85rem; margin-top: 4px;">
        Miễn giảm Giảng dạy: <b>{row['teaching_reduction_pct']}%</b> |
        Miễn giảm NCKH: <b>{row['nckh_reduction_pct']}%</b>
    </div>
</div>
            """
            render_list_item(content, 'reduction_rules', row['id'])

    with st.expander("Thêm Chức vụ Quản lý"):
        with st.form("add_role_form"):
            r_name = st.text_input("Tên chức vụ (VD: Trưởng phòng)")
            st.info("Cấu hình tỷ lệ phần trăm định mức nghĩa vụ được miễn giảm. Ví dụ: Nếu chức vụ được giảm 90% nghĩa vụ (chỉ cần thực hiện 10%), hãy nhập 90%.")
            r_teach = st.number_input("% Giờ chuẩn giảng dạy được miễn giảm", min_value=0.0, max_value=100.0, step=5.0)
            r_nckh = st.number_input("% Giờ NCKH được miễn giảm", min_value=0.0, max_value=100.0, step=5.0)

            if st.form_submit_button("Thêm"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO reduction_rules (name, rule_type, teaching_reduction_pct, nckh_reduction_pct) VALUES (?, 'ROLE', ?, ?)",
                                   (r_name, r_teach, r_nckh))
                    conn.commit()
                    st.success("Thêm thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

with tab5:
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">healing</span> Quy tắc Giảm định mức: Miễn giảm khác</h3>', unsafe_allow_html=True)

    df_specials = pd.read_sql_query("SELECT * FROM reduction_rules WHERE rule_type = 'SPECIAL'", conn)
    if df_specials.empty:
        render_empty_state("Chưa có diện miễn giảm nào.")
    else:
        for _, row in df_specials.iterrows():
            content = f"""
<div>
    <div style="color: var(--md-on-surface); font-weight: 600;">{row['name']}</div>
    <div style="color: var(--md-on-surface-variant); font-size: 0.85rem; margin-top: 4px;">
        Miễn giảm Giảng dạy: <b>{row['teaching_reduction_pct']}%</b> |
        Miễn giảm NCKH: <b>{row['nckh_reduction_pct']}%</b>
    </div>
</div>
            """
            render_list_item(content, 'reduction_rules', row['id'])

    with st.expander("Thêm Diện miễn giảm (Thai sản, học tập, v.v.)"):
        with st.form("add_special_form"):
            s_name = st.text_input("Tên diện miễn giảm")
            st.info("Cấu hình tỷ lệ phần trăm định mức nghĩa vụ được miễn giảm đối với đối tượng này. Ví dụ: đi học, thai sản được miễn 100%, hãy nhập 100%.")
            s_teach = st.number_input("% Giờ chuẩn giảng dạy được miễn giảm", min_value=0.0, max_value=100.0, step=5.0)
            s_nckh = st.number_input("% Giờ NCKH được miễn giảm", min_value=0.0, max_value=100.0, step=5.0)

            if st.form_submit_button("Thêm"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO reduction_rules (name, rule_type, teaching_reduction_pct, nckh_reduction_pct) VALUES (?, 'SPECIAL', ?, ?)",
                                   (s_name, s_teach, s_nckh))
                    conn.commit()
                    st.success("Thêm thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

with tab6:
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">list_alt</span> Danh mục Loại Hoạt động</h3>', unsafe_allow_html=True)

    df_acts = pd.read_sql_query("SELECT * FROM activity_types", conn)
    if df_acts.empty:
        render_empty_state("Chưa có loại hoạt động nào.")
    else:
        for _, row in df_acts.iterrows():
            cat_variant = "primary" if row['category'] == 'Giảng dạy' else ("green" if row['category'] == 'NCKH' else "amber")
            badge_html = f'<span class="md-chip md-chip-{cat_variant}">{row["category"]}</span>'
            content = f"""
<div>
    <div style="color: var(--md-on-surface); font-weight: 600;">{row['name']}</div>
    <div style="color: var(--md-on-surface-variant); font-size: 0.85rem; margin-top: 4px;">
        {badge_html}
        Đơn vị: <b>{row['unit']}</b> |
        Tỷ lệ: <b>{row['base_conversion_rate']}</b>
    </div>
</div>
            """
            render_list_item(content, 'activity_types', row['id'])

    with st.expander("Thêm Loại Hoạt động mới"):
        with st.form("add_act_form"):
            a_name = st.text_input("Tên Hoạt động (VD: Coi thi, Bài báo KH)")
            col1, col2 = st.columns(2)
            a_cat = col1.selectbox("Nhóm", ["Giảng dạy", "NCKH", "Hoạt động chuyên môn", "Chấp hành Nhiệm vụ khác"])
            a_unit = col2.text_input("Đơn vị tính (VD: Tiết, Bài, Đề tài)")

            a_rate = st.number_input("Tỷ lệ quy đổi (Ví dụ: 1 Bài báo = 30 giờ)", value=1.0, step=0.5)

            col_opts = st.columns(1)
            activity_group = col_opts[0].radio(
                "Phân loại tính chất hoạt động (cho nghĩa vụ chuẩn)", 
                ["Giảng dạy trực tiếp trên lớp (Tính vào nghĩa vụ dạy học chính)", "Nghiên cứu khoa học chính (Tính vào nghĩa vụ nghiên cứu)", "Hoạt động chuyên môn / Nhiệm vụ khác (Không tính vào nghĩa vụ chính trực tiếp)"], 
                index=0
            )
            is_teach = 1 if "Giảng dạy" in activity_group else 0
            is_nckh = 1 if "Nghiên cứu" in activity_group else 0

            if st.form_submit_button("Thêm"):
                try:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO activity_types (name, category, unit, base_conversion_rate, is_teaching_activity, is_nckh_activity)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (a_name, a_cat, a_unit, a_rate, int(is_teach), int(is_nckh)))
                    conn.commit()
                    st.success("Thêm thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

conn.close()
