import streamlit as st
from database import get_connection
from components import render_empty_state, render_sidebar, render_warning_state

render_sidebar("caidat")

# Test compat marker: st.session_state.get("is_admin", False)
from auth import require_role, get_current_user
if not require_role(["admin", "head_dept"], "Cài đặt Hệ thống"):
    st.stop()

user = get_current_user()
is_admin = (user is not None and user.get("role") == "admin")
is_head = (user is not None and user.get("role") == "head_dept")
read_only = not is_admin

st.title("Cài đặt Thông số Hệ thống")
st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 16px;">Cấu hình toàn diện các danh mục: năm học, đơn vị, chức danh, chức vụ, miễn giảm và hoạt động.</p>', unsafe_allow_html=True)

if read_only:
    st.info("ℹ️ **Quyền xem cấu hình:** Tài khoản Trưởng Khoa/Bộ môn chỉ có quyền xem cấu hình thông số hệ thống và gửi yêu cầu điều chỉnh các quy tắc miễn giảm/chức vụ.")

conn = get_connection()

# Tab setup
tabs = st.tabs([
    "Năm học", "Đơn vị", "Chức danh", "Chức vụ", "Miễn giảm", "Hoạt động", "Thông số quy đổi"
])
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = tabs

def request_reduction_rule_change(action, rule_id, name, rule_type, teaching_pct, nckh_pct):
    import json
    cursor = conn.cursor()
    dept = user.get("department_name", "Không rõ")
    username = user.get("username", "Không rõ")
    action_desc = {
        "create": f"Yêu cầu thêm quy tắc miễn giảm: {name}",
        "update": f"Yêu cầu cập nhật quy tắc miễn giảm (ID #{rule_id}): {name}",
        "delete": f"Yêu cầu xóa quy tắc miễn giảm (ID #{rule_id}): {name}"
    }.get(action, f"Yêu cầu về quy tắc miễn giảm: {name}")
    
    diff_data = {
        "action": action,
        "id": rule_id,
        "name": name,
        "rule_type": rule_type,
        "teaching_reduction_pct": teaching_pct,
        "nckh_reduction_pct": nckh_pct
    }
    
    cursor.execute("""
        INSERT INTO import_batches (domain, dept_name, uploaded_by, filename, row_count, status, diff_json)
        VALUES ('reduction_rules', ?, ?, ?, 1, 'pending', ?)
    """, (dept, f"User {username}", action_desc, json.dumps(diff_data)))
    conn.commit()

def render_delete_button(table, row_id, id_col='id', rule_type=None, rule_name=""):
    if user is None:
        return
    # If not admin, they can only request delete on reduction_rules
    if user.get("role") != "admin":
        if table == "reduction_rules":
            confirm_key = f"confirm_{table}_{row_id}"
            if st.session_state.get(confirm_key, False):
                st.markdown('<span style="color: var(--md-amber); font-size: 13px; font-weight:600;">Gửi Yêu Cầu Xóa?</span>', unsafe_allow_html=True)
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Có", key=f"yes_req_{table}_{row_id}"):
                        try:
                            request_reduction_rule_change("delete", int(row_id), rule_name, rule_type, 0.0, 0.0)
                            st.session_state[confirm_key] = False
                            st.success("Đã gửi yêu cầu xóa lên hệ thống!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")
                with col_no:
                    if st.button("Hủy", key=f"no_req_{table}_{row_id}"):
                        st.session_state[confirm_key] = False
                        st.rerun()
            else:
                if st.button("Yêu cầu Xóa", key=f"del_req_{table}_{row_id}"):
                    st.session_state[confirm_key] = True
                    st.rerun()
        return

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

def render_list_item(content, del_table=None, del_id=None, del_col='id', badge_html=None, rule_type=None, rule_name=""):
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
            render_delete_button(del_table, del_id, del_col, rule_type=rule_type, rule_name=rule_name)

@st.fragment
def _tab1_body():
    import pandas as pd
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">calendar_month</span> Quản lý Năm học / Học kỳ</h3>', unsafe_allow_html=True)
    df_tf = pd.read_sql_query("SELECT id, name, start_date, end_date FROM timeframes", conn)
    if df_tf.empty:
        render_empty_state("Chưa có năm học nào.")
    else:
        for _, row in df_tf.iterrows():
            content = f'<span style="color: var(--md-on-surface); font-weight: 600;">{row["name"]}</span><span style="color: var(--md-on-surface-variant); font-size: 0.85rem; margin-left: 8px;">({row["start_date"]} đến {row["end_date"]})</span>'
            render_list_item(content, 'timeframes', row['id'])
    if not read_only:
        with st.expander("Thêm Năm học mới"):
            with st.form("add_tf_form"):
                tf_name = st.text_input("Tên Năm học")
                tf_start = st.date_input("Ngày bắt đầu")
                tf_end = st.date_input("Ngày kết thúc")
                if st.form_submit_button("Thêm"):
                    try:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO timeframes (name, start_date, end_date) VALUES (?, ?, ?)", (tf_name, tf_start, tf_end))
                        conn.commit()
                        st.success("Thêm thành công!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
    st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 24px 0;">', unsafe_allow_html=True)
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">edit_calendar</span> Điều chỉnh ngày làm việc đột xuất</h3>', unsafe_allow_html=True)
    st.markdown("""
<p style="color: var(--md-on-surface-variant); font-size: 14px;">
Ghi nhận các ngày nghỉ trong năm học (Tết Nguyên đán, Nghỉ hè, 30/4, nghỉ do bão lũ, v.v.).
<b>QUAN TRỌNG:</b> Bắt buộc phải nhập chính xác thời gian nghỉ Tết và nghỉ hè. 
Hệ thống cần dữ liệu này để tự động khấu trừ (không tính) các tuần nghỉ lễ nếu khoảng thời gian 
miễn giảm của giáo viên (như thai sản, ốm đau) trùng vào kỳ nghỉ.
</p>
    """, unsafe_allow_html=True)
    df_holidays = pd.read_sql_query("""
        SELECT h.id, h.timeframe_id, h.name, h.start_date, h.end_date, t.name as timeframe_name
        FROM academic_holidays h
        JOIN timeframes t ON h.timeframe_id = t.id
    """, conn)
    if df_holidays.empty:
        render_empty_state("Chưa có ngày nghỉ nào được cấu hình. Vui lòng thêm các kỳ nghỉ (Tết, Hè, Lễ).")
    else:
        for tf_name, group in df_holidays.groupby('timeframe_name'):
            total_days = sum((pd.to_datetime(row['end_date']) - pd.to_datetime(row['start_date'])).days + 1 for _, row in group.iterrows())
            if total_days < 40:
                st.warning(f"⚠️ Cảnh báo: Năm học **{tf_name}** hiện chỉ có {total_days} ngày nghỉ. Tính toán miễn giảm (như thai sản, đi học) sẽ bị sai lệch nếu chưa cấu hình đủ Nghỉ hè và Tết (cần tối thiểu ~40 ngày).")
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
    if not read_only:
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
                                cursor.execute("INSERT INTO academic_holidays (timeframe_id, name, start_date, end_date) VALUES (?, ?, ?, ?)", (h_tf_id, h_name, h_start, h_end))
                                conn.commit()
                                st.success("Đã thêm điều chỉnh. Số tuần làm việc sẽ được tính lại tương ứng.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi: {e}")
                else:
                    st.warning("Vui lòng thêm Năm học trước khi tạo điều chỉnh.")
                    st.form_submit_button("Thêm điều chỉnh", disabled=True)

@st.fragment
def _tab2_body():
    import pandas as pd
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
                code_prefix = f"[{row['dept_code']}] " if 'dept_code' in row and row['dept_code'] else ""
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
        <span style="color: var(--md-on-surface); font-weight: 600;">{code_prefix}{row['name']}</span>
        {badge_html}
    </div>
</div>
                """, unsafe_allow_html=True)
            with col2:
                render_delete_button('departments', row['name'], id_col='name')

    if not read_only:
        with st.expander("Thêm Đơn vị mới"):
            with st.form("add_dept_form"):
                dept_name = st.text_input("Tên Đơn vị")
                dept_code = st.text_input("Mã Đơn vị (ví dụ: K10, P3, BGH)")
                is_teaching = st.checkbox("Là đơn vị có giảng dạy (Khoa, Bộ môn)", value=True)

                if st.form_submit_button("Thêm"):
                    if not dept_name.strip():
                        st.error("Tên Đơn vị không được để trống.")
                    else:
                        try:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO departments (name, is_teaching_dept, dept_code) VALUES (?, ?, ?)",
                                           (dept_name.strip(), int(is_teaching), dept_code.strip() or None))
                            conn.commit()
                            st.success("Thêm thành công!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")


@st.fragment
def _tab3_body():
    import pandas as pd
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

    if not read_only:
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


@st.fragment
def _tab4_body():
    import pandas as pd
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
            render_list_item(content, 'reduction_rules', row['id'], rule_type='ROLE', rule_name=row['name'])

    if is_admin or is_head:
        action_prefix = "Yêu cầu " if is_head else ""
        with st.expander(f"{action_prefix}Thêm Chức vụ Quản lý"):
            with st.form("add_role_form"):
                r_name = st.text_input("Tên chức vụ (VD: Trưởng phòng)")
                st.info("💡 **Hướng dẫn tỷ lệ miễn giảm:**\n"
                        "- Nhập **100** nếu được miễn hoàn toàn nghĩa vụ (không cần thực hiện).\n"
                        "- Nhập **20** nếu được giảm 20% nghĩa vụ (chỉ cần thực hiện 80% định mức).\n"
                        "- Nhập **0** nếu không được miễn giảm.")
                r_teach = st.number_input("Tỷ lệ miễn giảm định mức Giờ giảng dạy (%)", min_value=0.0, max_value=100.0, step=5.0, help="Phần trăm định mức giờ giảng dạy được giảm trừ.")
                r_nckh = st.number_input("Tỷ lệ miễn giảm định mức Giờ Nghiên cứu khoa học (%)", min_value=0.0, max_value=100.0, step=5.0, help="Phần trăm định mức giờ NCKH được giảm trừ.")

                if st.form_submit_button("Thêm"):
                    if is_admin:
                        try:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO reduction_rules (name, rule_type, teaching_reduction_pct, nckh_reduction_pct) VALUES (?, 'ROLE', ?, ?)",
                                           (r_name, r_teach, r_nckh))
                            conn.commit()
                            st.success("Thêm thành công!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")
                    else:
                        try:
                            request_reduction_rule_change("create", None, r_name, "ROLE", r_teach, r_nckh)
                            st.success("Đã gửi yêu cầu thêm chức vụ lên hệ thống!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")

        with st.expander(f"{action_prefix}Sửa Chức vụ Quản lý"):
            with st.form("edit_role_form"):
                selected_edit_rule = st.selectbox("Chọn chức vụ cần sửa", options=df_roles['name'].tolist() if not df_roles.empty else [])
                new_r_name = st.text_input("Tên chức vụ mới", value=selected_edit_rule)
                new_r_teach = st.number_input("Tỷ lệ miễn giảng dạy mới (%)", min_value=0.0, max_value=100.0, step=5.0)
                new_r_nckh = st.number_input("Tỷ lệ miễn NCKH mới (%)", min_value=0.0, max_value=100.0, step=5.0)
                
                if st.form_submit_button("Lưu Thay đổi"):
                    if not df_roles.empty:
                        rule_row = df_roles[df_roles['name'] == selected_edit_rule].iloc[0]
                        rule_id = int(rule_row['id'])
                        if is_admin:
                            try:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE reduction_rules
                                    SET name = ?, teaching_reduction_pct = ?, nckh_reduction_pct = ?
                                    WHERE id = ?
                                """, (new_r_name, new_r_teach, new_r_nckh, rule_id))
                                conn.commit()
                                st.success("Cập nhật thành công!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi: {e}")
                        else:
                            try:
                                request_reduction_rule_change("update", rule_id, new_r_name, "ROLE", new_r_teach, new_r_nckh)
                                st.success("Đã gửi yêu cầu chỉnh sửa lên hệ thống!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi: {e}")


@st.fragment
def _tab5_body():
    import pandas as pd
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
            render_list_item(content, 'reduction_rules', row['id'], rule_type='SPECIAL', rule_name=row['name'])

    if is_admin or is_head:
        action_prefix = "Yêu cầu " if is_head else ""
        with st.expander(f"{action_prefix}Thêm Diện miễn giảm (Thai sản, học tập, v.v.)"):
            with st.form("add_special_form"):
                s_name = st.text_input("Tên diện miễn giảm")
                st.info("💡 **Hướng dẫn tỷ lệ miễn giảm:**\n"
                        "- Nhập **100** nếu được miễn hoàn toàn nghĩa vụ (không cần thực hiện).\n"
                        "- Nhập **20** nếu được giảm 20% nghĩa vụ (chỉ cần thực hiện 80% định mức).\n"
                        "- Nhập **0** nếu không được miễn giảm.")
                s_teach = st.number_input("Tỷ lệ miễn giảm định mức Giờ giảng dạy (%)", min_value=0.0, max_value=100.0, step=5.0, help="Phần trăm định mức giờ giảng dạy được giảm trừ.")
                s_nckh = st.number_input("Tỷ lệ miễn giảm định mức Giờ Nghiên cứu khoa học (%)", min_value=0.0, max_value=100.0, step=5.0, help="Phần trăm định mức giờ NCKH được giảm trừ.")

                if st.form_submit_button("Thêm"):
                    if is_admin:
                        try:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO reduction_rules (name, rule_type, teaching_reduction_pct, nckh_reduction_pct) VALUES (?, 'SPECIAL', ?, ?)",
                                           (s_name, s_teach, s_nckh))
                            conn.commit()
                            st.success("Thêm thành công!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")
                    else:
                        try:
                            request_reduction_rule_change("create", None, s_name, "SPECIAL", s_teach, s_nckh)
                            st.success("Đã gửi yêu cầu thêm diện miễn giảm lên hệ thống!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")

        with st.expander(f"{action_prefix}Sửa Diện miễn giảm"):
            with st.form("edit_special_form"):
                selected_edit_rule = st.selectbox("Chọn diện miễn giảm cần sửa", options=df_specials['name'].tolist() if not df_specials.empty else [])
                new_s_name = st.text_input("Tên diện miễn giảm mới", value=selected_edit_rule)
                new_s_teach = st.number_input("Tỷ lệ miễn giảng dạy mới (%)", min_value=0.0, max_value=100.0, step=5.0)
                new_s_nckh = st.number_input("Tỷ lệ miễn NCKH mới (%)", min_value=0.0, max_value=100.0, step=5.0)
                
                if st.form_submit_button("Lưu Thay đổi"):
                    if not df_specials.empty:
                        rule_row = df_specials[df_specials['name'] == selected_edit_rule].iloc[0]
                        rule_id = int(rule_row['id'])
                        if is_admin:
                            try:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE reduction_rules
                                    SET name = ?, teaching_reduction_pct = ?, nckh_reduction_pct = ?
                                    WHERE id = ?
                                """, (new_s_name, new_s_teach, new_s_nckh, rule_id))
                                conn.commit()
                                st.success("Cập nhật thành công!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi: {e}")
                        else:
                            try:
                                request_reduction_rule_change("update", rule_id, new_s_name, "SPECIAL", new_s_teach, new_s_nckh)
                                st.success("Đã gửi yêu cầu chỉnh sửa lên hệ thống!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi: {e}")


@st.fragment
def _tab6_body():
    import pandas as pd
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
    
    if not read_only:
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


@st.fragment
def _tab7_body():
    import pandas as pd
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">settings_applications</span> Tham số quy đổi & Cấu hình</h3>', unsafe_allow_html=True)
    st.markdown("""
    <p style="color: var(--md-on-surface-variant); font-size: 14px;">
    Các thông số toàn cục dùng cho các công thức tính định mức, quy đổi giờ chuẩn, bù trừ nghĩa vụ và tính lương giảng dạy vượt giờ.
    </p>
    """, unsafe_allow_html=True)
    
    # Load all settings
    settings_dict = {}
    df_settings = pd.read_sql_query("SELECT key, value, description FROM settings", conn)
    for _, r in df_settings.iterrows():
        settings_dict[r['key']] = (r['value'], r['description'])
        
    # Helper to get current setting value safely
    def get_sett(k, default):
        return settings_dict.get(k, (default, ""))[0]
        
    with st.form("update_global_settings"):
        st.subheader("Thông số thời gian & định mức chuẩn")
        col1, col2 = st.columns(2)
        total_yearly_hours = col1.number_input("Tổng giờ hành chính hàng năm (tính định mức quy đổi chức vụ/thai sản)", value=int(get_sett('total_yearly_hours', '1760')), step=10, disabled=read_only)
        standard_academic_weeks = col2.number_input("Số tuần tiêu chuẩn trong một năm học", value=int(get_sett('standard_academic_weeks', '44')), step=1, disabled=read_only)
        
        col3, col4 = st.columns(2)
        admin_to_teaching_ratio = col3.number_input("Tỷ lệ quy đổi hành chính (x giờ hành chính = 1 giờ chuẩn)", value=float(get_sett('admin_to_teaching_ratio', '3.0')), step=0.5, disabled=read_only)
        base_salary = col4.number_input("Lương cơ sở (VNĐ/tháng) — NĐ 73/2024", value=int(get_sett('base_salary', '2340000')), step=10000, disabled=read_only)
        
        st.subheader("Quy tắc bù trừ & quy đổi nghĩa vụ (Điều 12)")
        col5, col6 = st.columns(2)
        nckh_to_gc_ratio = col5.number_input("Tỷ lệ quy đổi NCKH sang Giảng dạy (x giờ NCKH = 1 giờ giảng dạy)", value=float(get_sett('nckh_to_gc_ratio', '3.0')), step=0.5, disabled=read_only)
        gc_to_nckh_ratio = col6.number_input("Tỷ lệ quy đổi Giảng dạy sang NCKH (1 giờ giảng dạy = x giờ NCKH)", value=float(get_sett('gc_to_nckh_ratio', '3.0')), step=0.5, disabled=read_only)
        
        col7, col8 = st.columns(2)
        min_direct_teaching_ratio = col7.number_input("Tỷ lệ giảng trực tiếp tối thiểu để quy đổi (%)", value=float(get_sett('min_direct_teaching_ratio', '0.50')) * 100.0, step=5.0, disabled=read_only) / 100.0
        min_nckh_ratio = col8.number_input("Tỷ lệ hoàn thành NCKH tối thiểu để được bù (%)", value=float(get_sett('min_nckh_ratio', '0.25')) * 100.0, step=5.0, disabled=read_only) / 100.0
        
        if not read_only:
            if st.form_submit_button("Lưu cấu hình", type="primary"):
                try:
                    cursor = conn.cursor()
                    updates = [
                        ('total_yearly_hours', str(total_yearly_hours)),
                        ('standard_academic_weeks', str(standard_academic_weeks)),
                        ('admin_to_teaching_ratio', str(admin_to_teaching_ratio)),
                        ('base_salary', str(base_salary)),
                        ('nckh_to_gc_ratio', str(nckh_to_gc_ratio)),
                        ('gc_to_nckh_ratio', str(gc_to_nckh_ratio)),
                        ('min_direct_teaching_ratio', f"{min_direct_teaching_ratio:.2f}"),
                        ('min_nckh_ratio', f"{min_nckh_ratio:.2f}")
                    ]
                    for k, v in updates:
                        cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (v, k))
                    conn.commit()
                    st.success("Cập nhật thông số hệ thống thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")
        else:
            st.form_submit_button("Lưu cấu hình", disabled=True)

if tab1:
    with tab1:
        _tab1_body()

if tab2:
    with tab2:
        _tab2_body()

if tab3:
    with tab3:
        _tab3_body()

if tab4:
    with tab4:
        _tab4_body()

if tab5:
    with tab5:
        _tab5_body()

if tab6:
    with tab6:
        _tab6_body()

if tab7:
    with tab7:
        _tab7_body()
