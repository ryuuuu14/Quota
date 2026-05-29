import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import get_connection, delete_teacher
from components import render_empty_state, render_warning_state, render_sidebar, render_chip
from calculations import calculate_t04_weeks, get_timeframe_dates
from payroll import GUEST_RATES
from database import get_base_salary, compute_total_12m_salary, get_police_ranks

st.set_page_config(page_title="Quản lý Hồ sơ Nhà giáo", layout="wide")
render_sidebar("canbo")

st.title("Quản lý Hồ sơ Nhà giáo")
st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 16px;">Quản lý thông tin cơ bản và quá trình công tác của nhà giáo.</p>', unsafe_allow_html=True)

conn = get_connection()

# --- TOP: THÊM MỚI HỒ SƠ ---
with st.expander("➕ Thêm mới Hồ sơ Nhà giáo", expanded=False):
    df_titles = pd.read_sql_query("SELECT name FROM titles", conn)
    titles_list = df_titles['name'].tolist() if not df_titles.empty else ["(Chưa có dữ liệu)"]

    df_depts = pd.read_sql_query("SELECT name FROM departments", conn)
    depts_list = df_depts['name'].tolist() if not df_depts.empty else ["(Chưa có dữ liệu)"]

    df_roles = pd.read_sql_query("SELECT id, name FROM reduction_rules WHERE rule_type = 'ROLE'", conn)
    roles_dict = {row['name']: row['id'] for _, row in df_roles.iterrows()} if not df_roles.empty else {}
    roles_list = ["Không có"] + list(roles_dict.keys())

    # Load police ranks for selectbox
    police_ranks = get_police_ranks()
    police_rank_opts = {f"{r['rank_group']} — {r['rank_name']} (HS {r['coefficient']})": r for r in police_ranks}
    base_salary = get_base_salary()

    emp_type_opts = {"TEACHER": "Giảng viên cơ hữu", "GUEST": "Giảng viên thỉnh giảng", "STAFF": "Cán bộ quản lý"}
    create_emp_type = st.selectbox("Loại nhân sự", options=list(emp_type_opts.keys()), format_func=lambda x: emp_type_opts[x], key="create_emp_type")

    create_guest_rank = None
    create_police_rank_id = None
    create_coefficient = None
    create_salary = 0.0
    if st.session_state.create_emp_type == "GUEST":
        create_guest_rank = st.selectbox("Cấp bậc Khách mời", options=list(GUEST_RATES.keys()))
    else:
        selected_rank_key = st.selectbox(
            "Cấp bậc hàm",
            options=list(police_rank_opts.keys()),
            index=0,
            key="create_police_rank"
        )
        selected_rank = police_rank_opts[selected_rank_key]
        create_police_rank_id = selected_rank['id']
        create_coefficient = selected_rank['coefficient']
        computed_monthly = create_coefficient * base_salary
        computed_annual = computed_monthly * 12
        st.markdown(
            f'<div style="padding: 8px 12px; background: var(--md-surface-container); border-radius: var(--radius-md); '
            f'font-size: 0.9rem; line-height: 1.6;">'
            f'<strong>Hệ số:</strong> {create_coefficient} &nbsp;|&nbsp; '
            f'<strong>Lương tháng:</strong> {computed_monthly:,.0f} đ &nbsp;|&nbsp; '
            f'<strong>Tổng lương 12T:</strong> {computed_annual:,.0f} đ'
            f'</div>',
            unsafe_allow_html=True
        )

    with st.form("add_teacher_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Họ và tên")
        subject_group = col1.selectbox("Khối môn học", ["Tự nhiên/Kỹ thuật", "Chính trị/Nghiệp vụ"])
        is_female = col2.selectbox("Giới tính", ["Nam", "Nữ"]) == "Nữ"

        initial_title = col1.selectbox("Chức danh ban đầu", options=titles_list)
        initial_dept = col2.selectbox("Đơn vị công tác", options=depts_list)
        initial_role = col2.selectbox("Chức vụ ban đầu", options=roles_list)
        start_date = col2.date_input("Ngày bắt đầu công tác", value=date.today())

        if st.form_submit_button("Lưu Hồ sơ"):
            if not name.strip():
                st.error("Vui lòng nhập họ và tên.")
            elif initial_title == "(Chưa có dữ liệu)" or initial_dept == "(Chưa có dữ liệu)":
                st.error("Vui lòng cài đặt Chức danh và Đơn vị trong phần Cài đặt Hệ thống trước.")
            else:
                cursor = conn.cursor()
                is_guest = st.session_state.create_emp_type == "GUEST"
                cursor.execute("""
                    INSERT INTO teachers (name, subject_group, is_female, employment_type, guest_rank, total_12m_salary, police_rank_id, salary_coefficient)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (name.strip(), subject_group, int(is_female),
                      st.session_state.create_emp_type,
                      create_guest_rank if is_guest else None,
                      create_salary if is_guest else computed_annual,
                      create_police_rank_id if not is_guest else None,
                      create_coefficient if not is_guest else None))
                new_teacher_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
                    VALUES (?, 'TITLE', ?, NULL, ?, NULL)
                """, (new_teacher_id, initial_title, start_date.isoformat()))

                cursor.execute("""
                    INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
                    VALUES (?, 'DEPARTMENT', ?, NULL, ?, NULL)
                """, (new_teacher_id, initial_dept, start_date.isoformat()))

                if initial_role != "Không có":
                    role_id = roles_dict[initial_role]
                    cursor.execute("""
                        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
                        VALUES (?, 'REDUCTION', NULL, ?, ?, NULL)
                    """, (new_teacher_id, role_id, start_date.isoformat()))

                conn.commit()
                st.success("Đã thêm hồ sơ và khởi tạo lịch sử!")
                st.rerun()

st.markdown('<hr style="border-color: var(--md-outline-variant); margin: 16px 0;">', unsafe_allow_html=True)

# --- FETCH TEACHERS ---
df_teachers = pd.read_sql_query("""
    SELECT t.*, pr.rank_name
    FROM teachers t
    LEFT JOIN police_ranks pr ON t.police_rank_id = pr.id
    ORDER BY t.name
""", conn)

if df_teachers.empty:
    render_warning_state("Chưa có hồ sơ nhà giáo nào. Vui lòng thêm hồ sơ phía trên.")
else:
    # --- TWO COLUMN DASHBOARD ---
    col_left, col_right = st.columns([1, 2], gap="large")
    
    with col_left:
        # 1. Select Teacher
        teacher_opts = {f"{row['name']} ({row['subject_group']})": int(row['id']) for _, row in df_teachers.iterrows()}
        selected_teacher_name = st.selectbox("🔍 Chọn Nhà giáo", options=list(teacher_opts.keys()))
        selected_t_id = teacher_opts[selected_teacher_name]
        
        t_data = df_teachers[df_teachers['id'] == selected_t_id].iloc[0]
        
        # Fetch current status
        current_status_query = """
        SELECT h.record_type, h.value_text, r.name as rule_name, h.id as hist_id, r.rule_type, h.start_date
        FROM teacher_role_history h
        LEFT JOIN reduction_rules r ON h.reduction_rule_id = r.id
        WHERE h.teacher_id = ? AND h.end_date IS NULL
        """
        df_current = pd.read_sql_query(current_status_query, conn, params=[selected_t_id])
        curr_titles = df_current[df_current['record_type'] == 'TITLE']['value_text'].tolist()
        curr_depts = df_current[df_current['record_type'] == 'DEPARTMENT']['value_text'].tolist()
        
        c_title = curr_titles[0] if curr_titles else 'Chưa có chức danh'
        c_dept = curr_depts[0] if curr_depts else 'Chưa có đơn vị'
        gender = "Nữ" if t_data['is_female'] else "Nam"
        
        emp_type_labels = {"TEACHER": "Giảng viên cơ hữu", "GUEST": "Giảng viên thỉnh giảng", "STAFF": "Cán bộ quản lý"}
        emp_label = emp_type_labels.get(t_data['employment_type'], 'Chưa rõ')
        emp_type_variant = {"TEACHER": "primary", "GUEST": "amber", "STAFF": "green"}
        chip_variant = emp_type_variant.get(t_data['employment_type'], "primary")
        
        salary_info = ""
        rank_name = ""
        if t_data['employment_type'] == "GUEST":
            salary_info = f"Cấp bậc: {t_data['guest_rank']}"
        else:
            coeff = t_data['salary_coefficient'] if pd.notna(t_data['salary_coefficient']) else None
            sal = t_data['total_12m_salary'] if pd.notna(t_data['total_12m_salary']) else 0
            rank_name = t_data.get('rank_name', '')
            if coeff:
                rank_line = f"{rank_name} (HS {coeff})" if rank_name else f"Hệ số {coeff}"
                salary_info = f"{rank_line} &nbsp;|&nbsp; Lương 12T: {(coeff * base_salary * 12):,.0f} đ".replace(',', '.')
            elif sal > 0:
                salary_info = f"Lương 12T: {sal:,.0f} đ".replace(',', '.')
            else:
                salary_info = "Chưa cập nhật hệ số lương"

        # Summary Card
        salary_warning = ""
        coeff = t_data['salary_coefficient'] if pd.notna(t_data['salary_coefficient']) else None
        has_any_salary = coeff or (pd.notna(t_data['total_12m_salary']) and t_data['total_12m_salary'] > 0)
        if t_data['employment_type'] in ("TEACHER", "STAFF") and not has_any_salary:
            salary_warning = f'<div style="margin-top: 8px; padding: 6px 10px; background: #fff3cd; border-radius: 8px; font-size: 0.8rem; color: #92400e;">⚠️ Chưa có hệ số lương — không thể tính lương</div>'
        st.markdown(f"""<div style="
background: linear-gradient(135deg, var(--md-surface-container), var(--md-surface-container-low));
border-radius: 12px;
padding: 20px;
border: 1px solid var(--md-outline-variant);
box-shadow: 0 4px 6px rgba(0,0,0,0.05);
margin-bottom: 16px;
">
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
<div style="
width: 48px; height: 48px; border-radius: 50%; 
background: linear-gradient(135deg, var(--md-primary-container), var(--md-primary)); 
color: var(--md-on-primary);
display: flex; justify-content: center; align-items: center;
font-size: 24px; font-weight: bold;
">
{t_data['name'][0].upper()}
</div>
<div>
<h3 style="margin: 0; font-size: 1.1rem; color: var(--md-on-surface);">{t_data['name']}</h3>
<div style="font-size: 0.85rem; color: var(--md-on-surface-variant);">{gender} • {t_data['subject_group']} • {render_chip(emp_label, chip_variant)}</div>
</div>
</div>
<div style="font-size: 0.9rem; line-height: 1.6;">
<div><strong style="color: var(--md-primary);">🏛️ Đơn vị:</strong> {c_dept}</div>
<div><strong style="color: var(--md-primary);">💼 Chức danh:</strong> {c_title}</div>
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--md-outline-variant);">
<span style="font-weight: 500; white-space: nowrap;">{salary_info}</span>
</div>
{salary_warning}
</div>
</div>""", unsafe_allow_html=True)
        
        with st.expander("✏️ Chỉnh sửa Thông tin cơ bản", expanded=False):
            edit_emp_key = f"edit_emp_type_{selected_t_id}"
            if edit_emp_key not in st.session_state:
                st.session_state[edit_emp_key] = t_data['employment_type']
            
            emp_types = ["TEACHER", "GUEST", "STAFF"]
            emp_idx = emp_types.index(t_data['employment_type']) if t_data['employment_type'] in emp_types else 0
            new_emp = st.selectbox(
                "Loại nhân sự", emp_types, index=emp_idx,
                format_func=lambda x: {"TEACHER": "Giảng viên cơ hữu", "GUEST": "Giảng viên thỉnh giảng", "STAFF": "Cán bộ quản lý"}[x],
                key=edit_emp_key
            )
            
            new_guest_rank = t_data['guest_rank']
            new_police_rank_id = t_data['police_rank_id'] if pd.notna(t_data['police_rank_id']) else None
            new_coefficient = t_data['salary_coefficient'] if pd.notna(t_data['salary_coefficient']) else None
            new_salary = t_data['total_12m_salary'] if pd.notna(t_data['total_12m_salary']) else 0.0
            
            if st.session_state[edit_emp_key] == "GUEST":
                ranks = list(GUEST_RATES.keys())
                rank_idx = ranks.index(new_guest_rank) if new_guest_rank in ranks else 0
                new_guest_rank = st.selectbox("Cấp bậc Khách mời", ranks, index=rank_idx)
            else:
                rank_keys = list(police_rank_opts.keys())
                current_rank_key = None
                for k, r in police_rank_opts.items():
                    if r['id'] == new_police_rank_id:
                        current_rank_key = k
                        break
                if current_rank_key is None and new_coefficient:
                    current_rank_key = f"CMKT — (HS {new_coefficient})"
                    rank_keys = [current_rank_key] + rank_keys
                edit_rank_idx = rank_keys.index(current_rank_key) if current_rank_key in rank_keys else 0
                selected_edit_rank_key = st.selectbox(
                    "Cấp bậc hàm", options=rank_keys, index=edit_rank_idx,
                    key=f"edit_police_rank_{selected_t_id}"
                )
                selected_edit_rank = police_rank_opts.get(selected_edit_rank_key)
                if selected_edit_rank:
                    new_police_rank_id = selected_edit_rank['id']
                    new_coefficient = selected_edit_rank['coefficient']
                edit_monthly = (new_coefficient or 0) * base_salary
                edit_annual = edit_monthly * 12
                st.markdown(
                    f'<div style="padding: 8px 12px; background: var(--md-surface-container); border-radius: var(--radius-md); '
                    f'font-size: 0.9rem; line-height: 1.6;">'
                    f'<strong>Hệ số:</strong> {new_coefficient or "N/A"} &nbsp;|&nbsp; '
                    f'<strong>Lương tháng:</strong> {edit_monthly:,.0f} đ &nbsp;|&nbsp; '
                    f'<strong>Tổng lương 12T:</strong> {edit_annual:,.0f} đ'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            with st.form("edit_basic_info_form"):
                new_name = st.text_input("Họ và tên", value=t_data['name'])
                col_b1, col_b2 = st.columns(2)
                new_subj = col_b1.selectbox("Khối môn học", ["Tự nhiên/Kỹ thuật", "Chính trị/Nghiệp vụ"], index=0 if t_data['subject_group'] == "Tự nhiên/Kỹ thuật" else 1)
                new_fem = col_b2.selectbox("Giới tính", ["Nam", "Nữ"], index=1 if t_data['is_female'] else 0)
                
                if st.form_submit_button("Lưu thay đổi"):
                    cursor = conn.cursor()
                    is_edit_guest = st.session_state[edit_emp_key] == "GUEST"
                    cursor.execute("""
                        UPDATE teachers 
                        SET name = ?, subject_group = ?, is_female = ?, employment_type = ?,
                            guest_rank = ?, total_12m_salary = ?, police_rank_id = ?, salary_coefficient = ?
                        WHERE id = ?
                    """, (new_name, new_subj, 1 if new_fem == "Nữ" else 0,
                          st.session_state[edit_emp_key],
                          new_guest_rank if is_edit_guest else None,
                          new_salary if is_edit_guest else edit_annual,
                          new_police_rank_id if not is_edit_guest else None,
                          new_coefficient if not is_edit_guest else None,
                          selected_t_id))
                    conn.commit()
                    st.success("Đã cập nhật thông tin cơ bản!")
                    st.rerun()

    with col_right:
        # --- DYNAMIC ACTION FORM ---
        st.subheader("Cập nhật Quá trình Công tác")
        action_type = st.radio(
            "Loại điều chỉnh",
            ["Chức danh", "Đơn vị", "Chức vụ lãnh đạo", "Sự kiện miễn giảm", "Cấp bậc hàm"],
            horizontal=True, label_visibility="collapsed"
        )
        
        # Configure variables based on radio selection
        form_title = ""
        sql_opts = ""
        field_type = ""
        
        if action_type == "Chức danh":
            form_title = "Cập nhật Chức danh mới"
            sql_opts = "SELECT name FROM titles"
            field_type = "TITLE"
        elif action_type == "Đơn vị":
            form_title = "Chuyển Đơn vị công tác mới"
            sql_opts = "SELECT name FROM departments"
            field_type = "DEPARTMENT"
        elif action_type == "Chức vụ lãnh đạo":
            form_title = "Thêm Chức vụ Lãnh đạo mới"
            sql_opts = "SELECT id, name FROM reduction_rules WHERE rule_type = 'ROLE'"
            field_type = "ROLE"
        elif action_type == "Cấp bậc hàm":
            form_title = "Cập nhật Cấp bậc hàm (Ngạch lương)"
            field_type = "RANK"
        else:
            form_title = "Thêm Sự kiện Miễn giảm (Thai sản, Học tập, ...)"
            sql_opts = "SELECT id, name FROM reduction_rules WHERE rule_type = 'SPECIAL'"
            field_type = "SPECIAL"

        if field_type == "RANK":
            police_ranks = get_police_ranks()
            rank_opts = {f"{r['rank_group']} — {r['rank_name']} (HS {r['coefficient']})": r for r in police_ranks}
            rank_keys = list(rank_opts.keys())
            base_salary_rank = get_base_salary()
            with st.form("dynamic_form_RANK"):
                st.markdown(f"**{form_title}**")
                selected_rank_key = st.selectbox("Chọn Cấp bậc hàm mới", options=rank_keys)
                selected_rank = rank_opts[selected_rank_key]
                coeff = selected_rank['coefficient']
                monthly = coeff * base_salary_rank
                annual = monthly * 12
                st.markdown(
                    f'<div style="padding: 8px 12px; background: var(--md-surface-container); border-radius: var(--radius-md); '
                    f'font-size: 0.9rem; line-height: 1.6;">'
                    f'Hệ số: <strong>{coeff}</strong> | '
                    f'Lương tháng: <strong>{monthly:,.0f} đ</strong> | '
                    f'Lương 12T: <strong>{annual:,.0f} đ</strong>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                c1, c2 = st.columns(2)
                start_date_inner = c1.date_input("Ngày bổ nhiệm")
                rank_note = c2.text_input("Ghi chú (nếu có)", placeholder="Ví dụ: Xét nâng bậc lương")
                if st.form_submit_button("Lưu Cấp bậc hàm"):
                    if start_date_inner:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE teacher_rank_history
                            SET end_date = date(?, '-1 day')
                            WHERE teacher_id = ? AND end_date IS NULL
                        """, (start_date_inner.isoformat(), selected_t_id))
                        cursor.execute("""
                            INSERT INTO teacher_rank_history (teacher_id, police_rank_id, salary_coefficient, start_date, note)
                            VALUES (?, ?, ?, ?, ?)
                        """, (selected_t_id, selected_rank['id'], coeff, start_date_inner.isoformat(), rank_note))
                        cursor.execute("""
                            UPDATE teachers SET police_rank_id = ?, salary_coefficient = ? WHERE id = ?
                        """, (selected_rank['id'], coeff, selected_t_id))
                        conn.commit()
                        st.success("Đã cập nhật Cấp bậc hàm! Lương sẽ được tính theo tỷ lệ thời gian.")
                        st.rerun()
        else:
            df_opts = pd.read_sql_query(sql_opts, conn)
            options = df_opts['name'].tolist() if not df_opts.empty else ["(Chưa có dữ liệu)"]
            opts_dict = {}

            if field_type in ['ROLE', 'SPECIAL']:
                if field_type == 'ROLE':
                    unit_type = st.radio("Phạm vi công tác", ["Tại đơn vị giảng dạy", "Phòng/Trung tâm"], horizontal=True)
                    school_roles = ["Hiệu trưởng", "Phó Hiệu trưởng", "Phó Bí thư Đảng ủy Trường"]
                    if unit_type == "Tại đơn vị giảng dạy":
                        df_opts = df_opts[df_opts['name'].str.contains("Tại đơn vị giảng dạy") | df_opts['name'].isin(["Trưởng khoa", "Phó Trưởng khoa"] + school_roles)]
                    else:
                        df_opts = df_opts[df_opts['name'].str.contains("Công tác quản lý đảng") | df_opts['name'].isin(["Trưởng phòng", "Phó Trưởng phòng", "Công tác tại phòng, trung tâm không giữ chức vụ lãnh đạo"] + school_roles)]
                opts_dict = {f"{row['name']}": row['id'] for _, row in df_opts.iterrows()}
                options = list(opts_dict.keys()) if opts_dict else ["(Chưa có dữ liệu)"]

            with st.form(f"dynamic_form_{field_type}"):
                st.markdown(f"**{form_title}**")
                selected_val = st.selectbox("Chọn giá trị mới", options=options)
                
                c1, c2 = st.columns(2)
                start_date_inner = c1.date_input("Ngày bắt đầu hiệu lực")
                
                is_ongoing = True
                weeks_override = None
                if field_type in ['ROLE', 'SPECIAL']:
                    is_ongoing = c2.checkbox("Đang diễn ra", value=True)
                    end_date_inner = c2.date_input("Ngày kết thúc", disabled=is_ongoing)
                    
                    with st.expander("Ghi đè số tuần (Nâng cao)"):
                        use_override = st.checkbox("Ghi đè số tuần tự động")
                        if use_override:
                            weeks_override = st.number_input("Số tuần thực tế", min_value=0.0, max_value=52.0, value=44.0, step=0.5)
                            
                if st.form_submit_button("Lưu Lịch sử"):
                    if not options or options[0] == "(Chưa có dữ liệu)":
                        st.error("Vui lòng cài đặt danh mục trước.")
                    else:
                        active_rec = df_current[df_current['record_type'] == field_type] if field_type in ['TITLE', 'DEPARTMENT'] else df_current[df_current['rule_type'] == field_type]

                        if not active_rec.empty and active_rec.iloc[0]['start_date']:
                            try:
                                current_start = datetime.strptime(active_rec.iloc[0]['start_date'], '%Y-%m-%d').date()
                                if start_date_inner <= current_start:
                                    st.error(f"Ngày bắt đầu mới phải sau ngày bắt đầu của bản ghi hiện tại ({current_start})!")
                                    st.stop()
                            except Exception:
                                pass

                        cursor = conn.cursor()
                        if field_type in ['TITLE', 'DEPARTMENT']:
                            cursor.execute("UPDATE teacher_role_history SET end_date = date(?, '-1 day') WHERE teacher_id = ? AND record_type = ? AND end_date IS NULL", (start_date_inner.isoformat(), selected_t_id, field_type))
                            cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (?, ?, ?, ?)", (selected_t_id, field_type, selected_val, start_date_inner.isoformat()))
                        else:
                            rule_id = opts_dict[selected_val]
                            if field_type == 'ROLE':
                                cursor.execute("""
                                    UPDATE teacher_role_history
                                    SET end_date = date(?, '-1 day')
                                    WHERE teacher_id = ?
                                    AND end_date IS NULL
                                    AND reduction_rule_id IN (SELECT id FROM reduction_rules WHERE rule_type = 'ROLE')
                                """, (start_date_inner.isoformat(), selected_t_id))

                            cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, reduction_rule_id, start_date, end_date, actual_weeks_override) VALUES (?, 'REDUCTION', ?, ?, ?, ?)", (selected_t_id, rule_id, start_date_inner.isoformat(), None if is_ongoing else end_date_inner.isoformat(), weeks_override))
                        conn.commit()
                        st.success("Đã cập nhật lịch sử!")
                        st.rerun()

        st.markdown('<hr style="border-color: var(--md-outline-variant); margin: 16px 0;">', unsafe_allow_html=True)
        
        # --- HISTORY TIMELINE ---
        st.subheader("Toàn bộ quá trình công tác")
        role_query = """
            SELECT
                h.id,
                CASE
                    WHEN h.record_type = 'TITLE' THEN 'Chức danh'
                    WHEN h.record_type = 'DEPARTMENT' THEN 'Đơn vị'
                    WHEN r.rule_type = 'ROLE' THEN 'Chức vụ'
                    ELSE 'Sự kiện'
                END as "Loại",
                COALESCE(h.value_text, r.name) as "Chi tiết",
                h.start_date as "Từ ngày",
                COALESCE(h.end_date, 'Đến nay') as "Đến ngày",
                COALESCE(CAST(h.actual_weeks_override AS TEXT), 'Tự động') as "Số tuần thực tế"
            FROM teacher_role_history h
            LEFT JOIN reduction_rules r ON h.reduction_rule_id = r.id
            WHERE h.teacher_id = ?
        """
        rank_query = """
            SELECT
                rh.id + 100000 as id,
                'Cấp bậc hàm' as "Loại",
                pr.rank_name || ' (HS ' || rh.salary_coefficient || ')' as "Chi tiết",
                rh.start_date as "Từ ngày",
                COALESCE(rh.end_date, 'Đến nay') as "Đến ngày",
                '—' as "Số tuần thực tế"
            FROM teacher_rank_history rh
            JOIN police_ranks pr ON rh.police_rank_id = pr.id
            WHERE rh.teacher_id = ?
        """
        hist_df = pd.read_sql_query(role_query, conn, params=[selected_t_id])
        rank_hist_df = pd.read_sql_query(rank_query, conn, params=[selected_t_id])

        combined = pd.concat([hist_df, rank_hist_df], ignore_index=True)
        if not combined.empty:
            combined = combined.sort_values("Từ ngày", ascending=False)
            st.dataframe(combined, width='stretch', hide_index=True, use_container_width=True,
                column_config={
                    "Loại": st.column_config.Column(width="small"),
                    "Chi tiết": st.column_config.Column(width="large"),
                    "Từ ngày": st.column_config.Column(width="medium"),
                    "Đến ngày": st.column_config.Column(width="medium"),
                })
        else:
            st.info("Chưa có dữ liệu lịch sử.")

        # --- DANGER ZONE ---
        with st.expander("⚠️ Xóa dữ liệu lỗi / Xóa Hồ sơ"):
            # Delete History Row
            st.markdown("**Xóa dòng lịch sử bị lỗi**")
            df_all_hist = pd.read_sql_query("""
                SELECT h.id, h.record_type, COALESCE(h.value_text, r.name) as detail
                FROM teacher_role_history h
                LEFT JOIN reduction_rules r ON h.reduction_rule_id = r.id
                WHERE h.teacher_id = ?
            """, conn, params=[selected_t_id])

            if not df_all_hist.empty:
                del_opts = {f"[{row['record_type']}] {row['detail']}": row['id'] for _, row in df_all_hist.iterrows()}
                selected_del = st.selectbox("Chọn dòng lịch sử", options=list(del_opts.keys()), key="select_del_hist")
                del_id = del_opts[selected_del]
                
                if st.button("Xóa dòng lịch sử này", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM teacher_role_history WHERE id = ?", (del_id,))
                    conn.commit()
                    st.success("Đã xoá dòng lịch sử!")
                    st.rerun()
            else:
                st.caption("Không có lịch sử.")
                
            st.markdown("---")
            st.markdown("**Xóa toàn bộ hồ sơ nhà giáo này**")
            confirm_delete = st.checkbox("Tôi hiểu và xác nhận xóa vĩnh viễn toàn bộ dữ liệu.", key="confirm_delete_teacher_check")
            if st.button("Xóa vĩnh viễn Nhà giáo này", disabled=not confirm_delete, type="primary"):
                delete_teacher(selected_t_id)
                st.success("Đã xóa vĩnh viễn dữ liệu!")
                st.rerun()

conn.close()
