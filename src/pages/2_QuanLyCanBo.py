import streamlit as st
from datetime import date, datetime
from database import get_connection, delete_teacher
from components import render_empty_state, render_warning_state, render_sidebar, render_chip
from calculations import calculate_t04_weeks, get_timeframe_dates
from database import get_base_salary, compute_total_12m_salary, get_police_ranks

st.set_page_config(page_title="Quản lý Hồ sơ Nhà giáo", layout="wide")
render_sidebar("canbo")

st.title("Quản lý Hồ sơ Nhà giáo")
st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 16px;">Quản lý thông tin cơ bản và quá trình công tác của nhà giáo.</p>', unsafe_allow_html=True)

conn = get_connection()

# Fetch base salary globally to avoid NameError
base_raw = get_base_salary()
if not isinstance(base_raw, (int, float)):
    base_salary = 2340000.0
else:
    base_salary = float(base_raw)

# Load police ranks globally for selectboxes in both Edit and Create forms
police_ranks = get_police_ranks()
if not isinstance(police_ranks, list):
    police_ranks = []
if not police_ranks:
    police_rank_opts = {"(Chưa có cấp bậc hàm)": {'id': None, 'coefficient': 0.0, 'rank_name': '', 'rank_group': ''}}
else:
    police_rank_opts = {f"{r['rank_group']} — {r['rank_name']} (HS {r['coefficient']})": r for r in police_ranks}


# Check role/user permissions
from auth import get_current_user, get_scoped_teacher_ids, require_role
require_role(["admin", "head_dept"], "Quản lý Hồ sơ Nhà giáo")
user = get_current_user()
scoped_ids = get_scoped_teacher_ids(user)
is_admin = (user is not None and user["role"] == "admin")
is_head = (user is not None and user["role"] == "head_dept")


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
    border-radius: var(--radius-sm);
    padding: 10px 24px;
    border: 1px solid var(--md-outline-variant);
    color: var(--md-on-surface);
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    background-color: var(--md-primary-container);
    color: var(--md-primary) !important;
    border: 1px solid var(--md-primary-container);
}
.sp-card {
    background: var(--md-surface-container);
    border-radius: var(--radius-md);
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


# ── Helper: unified teacher profile card ──
def _render_teacher_profile_card(
    name, subject_group, teacher_id, employment_label, chip_variant,
    department, title, salary_info, salary_warning,
    highlighted=True,
):
    initial = name.split()[-1][0].upper()
    border = "2px solid var(--md-primary)" if highlighted else "1px solid var(--md-outline-variant)"
    background = "var(--md-primary-container)" if highlighted else "linear-gradient(135deg, var(--md-surface-container), var(--md-surface-container-low))"
    from components import render_chip
    return f"""<div style="background: {background}; border-radius: var(--radius-md); padding: 24px; border: {border}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 16px;">
<div style="display: flex; align-items: flex-start; gap: 12px; flex-wrap: wrap;">
<div style="width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, var(--md-primary-container), var(--md-primary)); color: var(--md-on-primary); display: flex; justify-content: center; align-items: center; font-size: 24px; font-weight: bold; flex-shrink: 0;">
{initial}
</div>
<div style="flex: 1; min-width: 160px; word-break: break-word;">
<h3 style="margin: 0 0 2px 0; font-size: 1.25rem; font-weight: 700; color: var(--md-primary); letter-spacing: 0.3px; word-break: break-word;">{name}</h3>
<div style="font-size: 0.85rem; color: var(--md-on-surface-variant);">{subject_group}<br>Mã: GV-{teacher_id}</div>
</div>
<div style="flex-shrink: 0;">{render_chip(employment_label, chip_variant)}</div>
</div>
<div style="border-top: 1px solid var(--md-outline-variant); margin: 14px 0 12px 0;"></div>
<div style="font-size: 0.9rem; line-height: 1.7;">
<div><strong style="color: var(--md-primary);">🏛️ Đơn vị:</strong> {department}</div>
<div><strong style="color: var(--md-primary);">💼 Chức danh:</strong> {title}</div>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--md-outline-variant);">
<span style="font-weight: 500; overflow-wrap: break-word; word-break: break-word;">{salary_info}</span>
</div>
{salary_warning}
</div>"""


tab1, tab2, tab3 = st.tabs([
    "📋 Danh sách & Tìm kiếm",
    "➕ Thêm mới Hồ sơ",
    "📥 Nhập dữ liệu từ Excel"
])

with tab1:
    import pandas as pd
    # --- FETCH TEACHERS ---
    df_teachers = pd.read_sql_query("""
        SELECT t.*, pr.rank_name
        FROM teachers t
        LEFT JOIN police_ranks pr ON t.police_rank_id = pr.id
        ORDER BY t.name
    """, conn)

    if scoped_ids is not None:
        df_teachers = df_teachers[df_teachers['id'].isin(scoped_ids)]

    if df_teachers.empty:
        render_warning_state("Chưa có hồ sơ nhà giáo nào. Vui lòng thêm hồ sơ phía trên.")
    else:
        # --- TWO COLUMN DASHBOARD ---
        col_left, col_right = st.columns([1, 2], gap="large")

        with col_left:
            # 1. Select Teacher — card list + compact selector
            teacher_list_items = []
            for _, row in df_teachers.iterrows():
                emp = row['employment_type']
                emp_label = {"TEACHER": "GV", "GUEST": "KM", "STAFF": "CB"}.get(emp, emp)
                teacher_list_items.append((row['name'], row['subject_group'], emp_label, int(row['id'])))

            if "teacher_selector" not in st.session_state:
                st.session_state["teacher_selector"] = teacher_list_items[0][0]

            st.markdown(f'<span style="font-size:12px;color:var(--md-on-surface-variant);">{len(teacher_list_items)} nhà giáo</span>',
                        unsafe_allow_html=True)

            names_list = [n for n, _, _, _ in teacher_list_items]
            cur_val = st.session_state["teacher_selector"]
            cur_idx = names_list.index(cur_val) if cur_val in names_list else 0
            selected_teacher_name = st.selectbox("Chọn nhà giáo", names_list, index=cur_idx,
                                                 key="teacher_selector", label_visibility="collapsed")

            teacher_id_map = {n: tid for n, _, _, tid in teacher_list_items}
            selected_t_id = teacher_id_map[selected_teacher_name]

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
            curr_roles = df_current[df_current['record_type'] == 'ROLE']['value_text'].tolist()
            if not curr_roles:
                curr_roles = df_current[df_current['rule_name'].notna()]['rule_name'].tolist()

            c_title = curr_titles[0] if curr_titles else 'Chưa có chức danh'
            c_dept = curr_depts[0] if curr_depts else 'Chưa có đơn vị'
            c_role = curr_roles[0] if curr_roles else None
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
                salary_warning = f'<div style="margin-top: 8px; padding: 6px 10px; background: #fff3cd; border-radius: var(--radius-sm); font-size: 0.8rem; color: #92400e;">⚠️ Chưa có hệ số lương — không thể tính lương</div>'
            st.markdown(
                _render_teacher_profile_card(
                    name=t_data['name'],
                    subject_group=t_data['subject_group'],
                    teacher_id=selected_t_id,
                    employment_label=emp_label,
                    chip_variant=chip_variant,
                    department=c_dept,
                    title=c_title,
                    salary_info=salary_info,
                    salary_warning=salary_warning,
                    highlighted=True,
                ),
                unsafe_allow_html=True,
            )


            if user is not None:
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
                        from payroll import GUEST_RATES
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
                            coeff_raw = selected_edit_rank.get('coefficient', 0.0)
                            if not isinstance(coeff_raw, (int, float)):
                                new_coefficient = 0.0
                            else:
                                new_coefficient = float(coeff_raw)
                        edit_monthly = (new_coefficient or 0.0) * base_salary
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
                        new_name = st.text_input("Họ và tên", value=t_data['name'], key=f"edit_name_{selected_t_id}")
                        col_b1, col_b2 = st.columns(2)
                        new_subj = col_b1.selectbox("Khối môn học", ["Tự nhiên/Kỹ thuật", "Chính trị/Nghiệp vụ"], index=0 if t_data['subject_group'] == "Tự nhiên/Kỹ thuật" else 1, key=f"edit_subj_{selected_t_id}")
                        new_fem = col_b2.selectbox("Giới tính", ["Nam", "Nữ"], index=1 if t_data['is_female'] else 0, key=f"edit_gender_{selected_t_id}")

                        if st.form_submit_button("Lưu thay đổi"):
                            cursor = conn.cursor()
                            is_edit_guest = st.session_state[edit_emp_key] == "GUEST"
                            if is_admin:
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
                            else:
                                # CRUD as request for Head Dept
                                cursor.execute("""
                                    INSERT INTO import_batches (domain, dept_name, status, uploaded_by, filename, row_count)
                                    VALUES ('teachers', ?, 'pending', ?, ?, 1)
                                """, (c_dept, f"User {user['username']}", f"Cập nhật thông tin {t_data['name']}", 1))
                                batch_id = cursor.lastrowid

                                cursor.execute("""
                                    INSERT INTO staging_teachers (
                                        batch_id, row_num, diff_marker, diff_detail, validation_errors,
                                        teacher_name, subject_group, is_female, employment_type,
                                        guest_rank, total_12m_salary, salary_coefficient, title, department, role, teacher_id
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    batch_id, 1, 'UPDATE', f"Chỉnh sửa thông tin cơ bản: {new_name}", "",
                                    new_name, new_subj, 1 if new_fem == "Nữ" else 0, st.session_state[edit_emp_key],
                                    new_guest_rank if is_edit_guest else None,
                                    new_salary if is_edit_guest else edit_annual,
                                    new_coefficient if not is_edit_guest else None,
                                    c_title, c_dept, c_role,
                                    selected_t_id
                                ))
                                conn.commit()
                                st.success(f"🎉 Đã gửi yêu cầu cập nhật thông tin cán bộ (Lô #{batch_id}) đến Quản trị viên phê duyệt!")
                                st.rerun()

        with col_right:
            if user is not None:
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
                    sql_opts = "SELECT id, name FROM reduction_rules WHERE rule_type = 'SPECIAL' AND name NOT LIKE 'Trợ giảng%'"
                    field_type = "SPECIAL"

                if field_type == "RANK":
                    if not is_admin:
                        st.warning("⚠️ Chỉ Quản trị viên hệ thống mới có quyền thay đổi Cấp bậc hàm (Ngạch lương).")
                    else:
                        police_ranks = get_police_ranks()
                        if not police_ranks:
                            rank_opts = {"(Chưa có cấp bậc hàm)": {'id': None, 'coefficient': 0.0, 'rank_name': '', 'rank_group': ''}}
                        else:
                            rank_opts = {f"{r['rank_group']} — {r['rank_name']} (HS {r['coefficient']})": r for r in police_ranks}
                        rank_keys = list(rank_opts.keys())
                        base_salary_rank = get_base_salary()
                        with st.form("dynamic_form_RANK"):
                            st.markdown(f"**{form_title}**")
                            selected_rank_key = st.selectbox("Chọn Cấp bậc hàm mới", options=rank_keys)
                            selected_rank = rank_opts.get(selected_rank_key, {'id': None, 'coefficient': 0.0})
                            coeff = selected_rank.get('coefficient', 0.0)
                            monthly = (coeff or 0.0) * base_salary_rank
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
                    if field_type == "SPECIAL" and not is_admin:
                        st.warning("⚠️ Chỉ Quản trị viên hệ thống mới có quyền thêm Sự kiện miễn giảm.")
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
                                    if is_admin:
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
                                    else:
                                        # Submit UPDATE request for head_dept
                                        target_title = selected_val if field_type == "TITLE" else c_title
                                        target_dept = selected_val if field_type == "DEPARTMENT" else c_dept
                                        target_role = selected_val if field_type == "ROLE" else c_role

                                        cursor.execute("""
                                            INSERT INTO import_batches (domain, dept_name, status, uploaded_by, filename, row_count)
                                            VALUES ('teachers', ?, 'pending', ?, ?, 1)
                                        """, (c_dept, f"User {user['username']}", f"Yêu cầu điều chỉnh {action_type} - {t_data['name']}", 1))
                                        batch_id = cursor.lastrowid

                                        cursor.execute("""
                                            INSERT INTO staging_teachers (
                                                batch_id, row_num, diff_marker, diff_detail, validation_errors,
                                                teacher_name, subject_group, is_female, employment_type,
                                                guest_rank, total_12m_salary, salary_coefficient, title, department, role, teacher_id
                                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (
                                            batch_id, 1, 'UPDATE', f"Yêu cầu điều chỉnh {action_type} thành: {selected_val}", "",
                                            t_data['name'], t_data['subject_group'], int(t_data['is_female']), t_data['employment_type'],
                                            t_data['guest_rank'], t_data['total_12m_salary'], t_data['salary_coefficient'],
                                            target_title, target_dept, target_role,
                                            selected_t_id
                                        ))
                                        conn.commit()
                                        st.success(f"🎉 Đã gửi yêu cầu điều chỉnh {action_type} (Lô #{batch_id}) đến Quản trị viên phê duyệt!")
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

            # Virtualize Trợ giảng default reductions in the timeline
            cursor = conn.cursor()
            cursor.execute("""
                SELECT start_date FROM teacher_role_history
                WHERE teacher_id = ? AND record_type = 'TITLE' AND value_text = 'Trợ giảng'
            """, (selected_t_id,))
            tro_giang_rows = cursor.fetchall()

            virtual_rows = []
            for (start_str,) in tro_giang_rows:
                if start_str:
                    app_date = pd.to_datetime(start_str)
                    t12_start = app_date
                    t12_end = app_date + pd.DateOffset(months=12) - pd.Timedelta(days=1)
                    t24_start = app_date + pd.DateOffset(months=12)
                    t24_end = app_date + pd.DateOffset(months=24) - pd.Timedelta(days=1)

                    virtual_rows.append({
                        "id": -1,
                        "Loại": "Sự kiện",
                        "Chi tiết": "Trợ giảng (12 tháng đầu) — Mặc định giảm 50% định mức",
                        "Từ ngày": t12_start.strftime('%Y-%m-%d'),
                        "Đến ngày": t12_end.strftime('%Y-%m-%d'),
                        "Số tuần thực tế": "Tự động"
                    })
                    virtual_rows.append({
                        "id": -2,
                        "Loại": "Sự kiện",
                        "Chi tiết": "Trợ giảng (tháng 13-24) — Mặc định giảm 20% định mức",
                        "Từ ngày": t24_start.strftime('%Y-%m-%d'),
                        "Đến ngày": t24_end.strftime('%Y-%m-%d'),
                        "Số tuần thực tế": "Tự động"
                    })

            if virtual_rows:
                v_df = pd.DataFrame(virtual_rows)
                combined = pd.concat([combined, v_df], ignore_index=True)

            if not combined.empty:
                _asc = combined.sort_values("Từ ngày", ascending=True)
                _seen_types = set()
                _prefix_map = {}
                for idx in _asc.index:
                    _type = combined.at[idx, "Loại"]
                    _is_first = _type not in _seen_types
                    _seen_types.add(_type)
                    _prefix_map[idx] = _is_first
                combined = combined.sort_values("Từ ngày", ascending=True)
                tl_colors = {"Chức danh": "#FFC107", "Đơn vị": "#4A5D23", "Chức vụ": "#C9A84C",
                            "Cấp bậc hàm": "#800020", "Sự kiện": "#8A7F75"}
                tl_html = '<div style="position:relative;padding-left:24px;">'
                tl_html += '<div style="position:absolute;left:7px;top:8px;bottom:8px;width:2px;background:var(--md-outline-variant);"></div>'
                for _, row in combined.iterrows():
                    color = tl_colors.get(row["Loại"], "#6b7280")
                    _is_first = _prefix_map.get(row.name, True)
                    _prefixes = {"Chức danh": "Thay đổi chức danh", "Đơn vị": "Chuyển đơn vị",
                                 "Chức vụ": "Bổ nhiệm", "Cấp bậc hàm": "Thay đổi cấp bậc hàm", "Sự kiện": ""}
                    _prefix = _prefixes.get(row["Loại"], "")
                    _detail = f"{_prefix}: {row['Chi tiết']}" if (_prefix and not _is_first) else row["Chi tiết"]
                    tl_html += f"""
                    <div style="position:relative;padding:0 0 16px 16px;">
                        <div style="position:absolute;left:-17px;top:6px;width:14px;height:14px;
                            border-radius:50%;background:{color};border:2px solid white;
                            box-shadow:0 0 0 1px {color};"></div>
                        <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;">
                            <div>
                                <span style="font-size:11px;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:0.3px;">{row["Loại"]}</span>
                                <div style="font-size:14px;font-weight:500;color:var(--md-on-surface);margin-top:2px;">{_detail}</div>
                            </div>
                            <div style="text-align:right;flex-shrink:0;">
                                <div style="font-size:12px;color:var(--md-on-surface-variant);">{row["Từ ngày"]}</div>
                                <div style="font-size:11px;color:var(--md-outline);">→ {row["Đến ngày"]}</div>
                            </div>
                        </div>
                    </div>"""
                tl_html += '</div>'
                st.markdown(tl_html, unsafe_allow_html=True)
            else:
                st.info("Chưa có dữ liệu lịch sử.")

            # --- DANGER ZONE ---
            if user is not None:
                with st.expander("⚠️ Xóa dữ liệu lỗi / Xóa Hồ sơ"):
                    # Delete History Row
                    st.markdown("**Xóa dòng lịch sử bị lỗi**")
                    if not is_admin:
                        st.warning("⚠️ Chỉ Quản trị viên hệ thống mới có quyền xóa dòng lịch sử.")
                    else:
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
                        if is_admin:
                            delete_teacher(selected_t_id)
                            st.success("Đã xóa vĩnh viễn dữ liệu!")
                            st.rerun()
                        else:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO import_batches (domain, dept_name, status, uploaded_by, filename, row_count)
                                VALUES ('teachers', ?, 'pending', ?, ?, 1)
                            """, (c_dept, f"User {user['username']}", f"Yêu cầu xóa hồ sơ - {t_data['name']}", 1))
                            batch_id = cursor.lastrowid

                            cursor.execute("""
                                INSERT INTO staging_teachers (
                                    batch_id, row_num, diff_marker, diff_detail, validation_errors,
                                    teacher_name, subject_group, is_female, employment_type,
                                    guest_rank, total_12m_salary, salary_coefficient, title, department, role, teacher_id
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                batch_id, 1, 'DELETE', f"Yêu cầu xóa toàn bộ hồ sơ của nhà giáo: {t_data['name']}", "",
                                t_data['name'], t_data['subject_group'], int(t_data['is_female']), t_data['employment_type'],
                                t_data['guest_rank'], t_data['total_12m_salary'], t_data['salary_coefficient'],
                                c_title, c_dept, c_role,
                                selected_t_id
                            ))
                            conn.commit()
                            st.success(f"🎉 Đã gửi yêu cầu xóa hồ sơ nhà giáo (Lô #{batch_id}) đến Quản trị viên phê duyệt!")
                            st.rerun()


with tab2:
    # --- TOP: THÊM MỚI HỒ SƠ ---
    if user is not None:
        with st.expander("➕ Thêm mới Hồ sơ Nhà giáo", expanded=False):
            df_titles = pd.read_sql_query("SELECT name FROM titles", conn)
            titles_list = df_titles['name'].tolist() if not df_titles.empty else ["(Chưa có dữ liệu)"]

            df_depts = pd.read_sql_query("SELECT name FROM departments", conn)
            depts_list = df_depts['name'].tolist() if not df_depts.empty else ["(Chưa có dữ liệu)"]
            if is_head:
                depts_list = [user["department_name"]]

            df_roles = pd.read_sql_query("SELECT id, name FROM reduction_rules WHERE rule_type = 'ROLE'", conn)
            roles_dict = {row['name']: row['id'] for _, row in df_roles.iterrows()} if not df_roles.empty else {}
            roles_list = ["Không có"] + list(roles_dict.keys())




            emp_type_opts = {"TEACHER": "Giảng viên cơ hữu", "GUEST": "Giảng viên thỉnh giảng", "STAFF": "Cán bộ quản lý"}
            create_emp_type = st.selectbox("Loại nhân sự", options=list(emp_type_opts.keys()), format_func=lambda x: emp_type_opts[x], key="create_emp_type")

            create_guest_rank = None
            create_police_rank_id = None
            create_coefficient = None
            create_salary = 0.0
            if st.session_state.create_emp_type == "GUEST":
                from payroll import GUEST_RATES
                create_guest_rank = st.selectbox("Cấp bậc Khách mời", options=list(GUEST_RATES.keys()))
            else:
                selected_rank_key = st.selectbox(
                    "Cấp bậc hàm",
                    options=list(police_rank_opts.keys()),
                    index=0,
                    key="create_police_rank"
                )
                selected_rank = police_rank_opts.get(selected_rank_key, {'id': None, 'coefficient': 0.0})
                create_police_rank_id = selected_rank.get('id')
                coeff_raw = selected_rank.get('coefficient', 0.0)
                if not isinstance(coeff_raw, (int, float)):
                    create_coefficient = 0.0
                else:
                    create_coefficient = float(coeff_raw)
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
                        if is_admin:
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
                        else:
                            # CRUD as request for Head Dept
                            cursor.execute("""
                                INSERT INTO import_batches (domain, dept_name, status, uploaded_by, filename, row_count)
                                VALUES ('teachers', ?, 'pending', ?, ?, 1)
                            """, (initial_dept, f"User {user['username']}", "Thêm mới cán bộ", 1))
                            batch_id = cursor.lastrowid

                            cursor.execute("""
                                INSERT INTO staging_teachers (
                                    batch_id, row_num, diff_marker, diff_detail, validation_errors,
                                    teacher_name, subject_group, is_female, employment_type,
                                    guest_rank, total_12m_salary, salary_coefficient, title, department, role, teacher_id
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                batch_id, 1, 'NEW', "Thêm cán bộ mới trực tiếp từ giao diện", "",
                                name.strip(), subject_group, int(is_female), st.session_state.create_emp_type,
                                create_guest_rank if is_guest else None,
                                create_salary if is_guest else computed_annual,
                                create_coefficient if not is_guest else None,
                                initial_title, initial_dept,
                                initial_role if initial_role != "Không có" else None,
                                None
                            ))
                            conn.commit()
                            st.success(f"🎉 Đã gửi yêu cầu thêm cán bộ (Lô #{batch_id}) đến Quản trị viên phê duyệt!")
                            st.rerun()

    st.markdown('<hr style="border-color: var(--md-outline-variant); margin: 16px 0;">', unsafe_allow_html=True)


with tab3:
    # --- TOP: NHẬP HÀNG LOẠT ---
    if is_admin or is_head:
        df_depts_list = pd.read_sql_query("SELECT name FROM departments", conn)
        depts_list_opts = df_depts_list['name'].tolist() if not df_depts_list.empty else []

        if is_admin:
            dept_name = st.selectbox("Chọn Đơn vị nhập dữ liệu:", options=depts_list_opts, key="admin_upload_dept")
            dept_auth_code = "Admin"
        else:
            dept_name = user["department_name"]
            dept_auth_code = "HeadDept"
            st.success(f"✓ Đơn vị thực hiện: **{dept_name}**")

        if dept_name:
            selected_sheet = None
            header_row = 0
            file_bytes = None
            uploaded_teachers = None

            # ── Stepper ──
            stepper_steps = ["Tải lên", "Ghép cột", "Kiểm tra", "Gửi"]
            if "import_step_teachers" not in st.session_state:
                st.session_state.import_step_teachers = 1

            step_html = '<div style="display:flex;gap:4px;margin:16px 0;padding:8px 0;border-top:1px solid var(--md-outline-variant);border-bottom:1px solid var(--md-outline-variant);">'
            for i, label in enumerate(stepper_steps):
                sn = i + 1
                is_active = sn == st.session_state.import_step_teachers
                is_done = sn < st.session_state.import_step_teachers
                bg = "var(--md-primary)" if is_active else "var(--md-primary-container)" if is_done else "var(--md-surface-dim)"
                c = "#fff" if is_active else "var(--md-primary)" if is_done else "var(--md-on-surface-variant)"
                check = "✓ " if is_done else ""
                step_html += f'<div style="flex:1;text-align:center;padding:6px 4px;border-radius:var(--radius-md);background:{bg};border:1px solid var(--md-outline-variant);">'
                step_html += f'<span style="font-size:12px;font-weight:600;color:{c};">{check}{label}</span></div>'
            step_html += '</div>'
            st.markdown(step_html, unsafe_allow_html=True)

            # ── Step 1: Tải lên ──
            if st.session_state.import_step_teachers == 1:
                from pipeline.templates import generate_teachers_template
                st.markdown("#### Hướng dẫn nhập dữ liệu:")
                st.markdown("""
                1. Tải file mẫu Excel được cấu hình riêng cho đơn vị của bạn.
                2. Điền đầy đủ thông tin cán bộ theo mẫu.
                3. Tải lên file đã điền để kiểm tra và gửi yêu cầu phê duyệt cho Quản trị viên.
                """)
                try:
                    template_bytes = generate_teachers_template(dept_name)
                    st.download_button(
                        label=f"📥 Tải file mẫu Excel ({dept_name})",
                        data=template_bytes,
                        file_name=f"Mau_Can_Bo_{dept_name.replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_teachers_template_btn",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Lỗi tạo file mẫu: {e}")

                if st.button("Tiếp theo →", key="step1_next_teachers"):
                    st.session_state.import_step_teachers = 2
                    st.rerun()

            st.info("💡 **Mẹo:** Bạn có thể tải lên bất kỳ bảng Excel nào. Hệ thống hỗ trợ tính năng tự động nhận diện tiêu đề cột thông minh.")
            st.markdown("---")
            st.markdown("##### Tải lên file Excel dữ liệu:")
            uploaded_teachers = st.file_uploader(
                "Chọn file Excel đã điền:",
                type=["xlsx", "xls"],
                label_visibility="collapsed",
                key="uploaded_teachers_excel"
            )

            # ── Content (upload → mapping → validation → submit) ──
            if uploaded_teachers is not None:
                if uploaded_teachers.size > 5 * 1024 * 1024:
                    st.error("❌ File tải lên vượt quá giới hạn dung lượng cho phép (5MB). Vui lòng thử lại với file nhỏ hơn.")
                else:
                    file_bytes = uploaded_teachers.read()
                    from pipeline.importer import parse_excel_to_df, get_excel_sheet_names, get_excel_headers, remap_dataframe_columns
                    from pipeline.fuzzy_matcher import match_columns
                    from pipeline.validator import validate_teachers_data
                    from pipeline.differ import diff_teachers
                    from pipeline.mapping_templates import load_mapping_templates, save_mapping_template, delete_mapping_template

                    try:
                        sheet_names = get_excel_sheet_names(file_bytes)

                        # Auto-detect header row
                        def _auto_detect_header_row(file_bytes, sheet_name):
                            import pandas as pd, io
                            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=None, nrows=30)
                            known = {"mã gv", "họ tên", "họ và tên", "đơn vị", "chức vụ", "chức danh",
                                     "tổ bộ môn", "loại hợp đồng", "giới tính", "ngày sinh",
                                     "cấp bậc", "học hàm", "số cmnd", "cccd", "email",
                                     "thời gian bổ nhiệm", "ngày bổ nhiệm", "thời gian đi học",
                                     "thời gian đi thực tế", "thời gian nghỉ có phép"}
                            best_row, best_score = 0, 0
                            for idx in range(min(21, len(df))):
                                cells = [str(c).strip().lower() for c in df.iloc[idx] if pd.notna(c)]
                                score = sum(1 for c in cells if any(k in c for k in known))
                                if score > best_score:
                                    best_score, best_row = score, idx
                            return best_row

                        selected_sheet = sheet_names[0]
                        header_row = _auto_detect_header_row(file_bytes, selected_sheet)

                        col_sh, col_hd = st.columns(2)
                        with col_sh:
                            selected_sheet = st.selectbox(
                                "Chọn Sheet cần đọc:",
                                options=sheet_names,
                                index=0,
                                key="import_selected_sheet_sel"
                            )
                        with col_hd:
                            header_row = st.number_input(
                                "Dòng chứa tiêu đề (0-indexed):",
                                min_value=0,
                                max_value=20,
                                value=header_row,
                                step=1,
                                key="import_header_row_val"
                            )

                        st.markdown("---")

                        headers = get_excel_headers(file_bytes, sheet_name=selected_sheet, header_row=header_row)
                        if not headers:
                            st.error("Không tìm thấy tiêu đề cột nào tại dòng đã chọn.")
                        else:
                            required_cols = [
                                "Mã GV", "Họ tên", "Đơn vị", "Chức vụ", "Ngày bổ nhiệm chức vụ",
                                "Chức danh", "Ngày bổ nhiệm chức danh"
                            ]
                            optional_cols = [
                                "Thời gian đi học", "Thời gian đi thực tế", "Thời gian nghỉ có phép"
                            ]
                            all_target_cols = required_cols + optional_cols

                            saved_templates = load_mapping_templates()
                            template_options = ["(Chọn cấu hình đã lưu)"] + list(saved_templates.keys())

                            col_tpl_sel, col_tpl_del = st.columns([3, 1])
                            with col_tpl_sel:
                                selected_tpl = st.selectbox(
                                    "Sử dụng cấu hình cột đã lưu:",
                                    options=template_options,
                                    key="selected_mapping_template_name"
                                )
                            with col_tpl_del:
                                st.write("")
                                st.write("")
                                if selected_tpl != "(Chọn cấu hình đã lưu)":
                                    if st.button("🗑️ Xóa cấu hình này", key="delete_tpl_btn"):
                                        delete_mapping_template(selected_tpl)
                                        st.success(f"Đã xóa cấu hình '{selected_tpl}'")
                                        st.rerun()

                            # Retrieve defaults with structured result
                            if selected_tpl != "(Chọn cấu hình đã lưu)":
                                defaults = saved_templates[selected_tpl]
                                match_result = None
                            else:
                                match_result = match_columns(headers, all_target_cols,
                                    required_columns=required_cols,
                                    return_format="structured")
                                defaults = match_result.to_legacy_dict()

                            # --- Initialize session mapping ---
                            mapping_key = f"_excel_mapping_{hash(file_bytes)}_{selected_tpl}_teachers"
                            if mapping_key not in st.session_state:
                                st.session_state[mapping_key] = dict(defaults)
                            current_mapping = st.session_state[mapping_key]

                            # --- Load sample data once ---
                            def _load_sample_data(file_bytes, sheet_name, header_row, headers):
                                try:
                                    import pandas as pd
                                    df = pd.read_excel(file_bytes, sheet_name=sheet_name, header=header_row, nrows=1)
                                    if df.empty:
                                        return {}
                                    return {h: df.iloc[0].get(h, "") for h in headers}
                                except Exception:
                                    return {}

                            sample_key = f"_sample_data_{hash(file_bytes)}_{selected_sheet}_{header_row}"
                            if sample_key not in st.session_state:
                                st.session_state[sample_key] = _load_sample_data(
                                    file_bytes, selected_sheet, header_row, headers
                                )

                            # CSS for layout indicator dot/badge
                            st.markdown("""<style>
                            .sp-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; display:inline-block; vertical-align:middle; margin-right:6px; }
                            .sp-dot.g { background:#22c55e; }
                            .sp-dot.y { background:#eab308; }
                            .sp-dot.r { background:#ef4444; }
                            .sp-badge { background:#ef4444; color:#fff; font-size:9px; padding:1px 5px; border-radius:3px; margin-left:4px; font-weight:600; white-space:nowrap; }
                            .sp-preview { border-left:1px solid #e5e7eb; padding-left:16px; }
                            </style>""", unsafe_allow_html=True)

                            # --- Split panel: mapping + data preview ---
                            col_left, col_right = st.columns([0.4, 0.6])

                            with col_left:
                                st.caption("GHEP CỘT")
                                col_map = {m.expected_column: m for m in (match_result.mappings if match_result else [])}
                                req_cols_list = required_cols
                                opt_cols_list = optional_cols

                                for col in req_cols_list:
                                    m = col_map.get(col)
                                    val = current_mapping.get(col)
                                    is_missing = val is None
                                    dot = "r" if is_missing else ("g" if m and m.confidence >= 90 else "y")

                                    rc = st.columns([0.3, 1.5, 2.8])
                                    with rc[0]:
                                        st.markdown(f'<span class="sp-dot {dot}"></span>', unsafe_allow_html=True)
                                    with rc[1]:
                                        st.markdown(f'<span style="font-size:13px;font-weight:500;">{col}<span class="sp-badge">BẮT BUỘC</span></span>',
                                                    unsafe_allow_html=True)
                                    with rc[2]:
                                        di = 0
                                        cur = current_mapping.get(col)
                                        if cur in headers:
                                            di = headers.index(cur) + 1
                                        elif m and m.matched_header in headers:
                                            di = headers.index(m.matched_header) + 1
                                        sel = st.selectbox("", ["(Không chọn)"] + headers, index=di,
                                                           key=f"sp_req_{col}", label_visibility="collapsed")
                                        current_mapping[col] = None if sel == "(Không chọn)" else sel

                                if opt_cols_list:
                                    with st.expander(f"Không bắt buộc ({len(opt_cols_list)} trường)", expanded=False):
                                        for col in opt_cols_list:
                                            m = col_map.get(col)
                                            val = current_mapping.get(col)
                                            dot = "g" if m and m.confidence >= 90 else "y" if m and m.confidence >= 50 else "r"

                                            oc = st.columns([0.3, 1.5, 2.8])
                                            with oc[0]:
                                                st.markdown(f'<span class="sp-dot {dot}"></span>', unsafe_allow_html=True)
                                            with oc[1]:
                                                st.markdown(f'<span style="font-size:13px;">{col}</span>', unsafe_allow_html=True)
                                            with oc[2]:
                                                di = 0
                                                cur = current_mapping.get(col)
                                                if cur in headers:
                                                    di = headers.index(cur) + 1
                                                elif m and m.matched_header in headers:
                                                    di = headers.index(m.matched_header) + 1
                                                sel = st.selectbox("", ["(Không chọn)"] + headers, index=di,
                                                                   key=f"sp_opt_{col}", label_visibility="collapsed")
                                                current_mapping[col] = None if sel == "(Không chọn)" else sel

                                missing_req = [c for c in required_cols if current_mapping.get(c) is None]
                                if missing_req:
                                    st.markdown(f'<span style="color:#dc2626;font-size:13px;">Thiếu {len(missing_req)} cột bắt buộc</span>',
                                                unsafe_allow_html=True)

                                if match_result and match_result.unmatched_excel_headers:
                                    u = match_result.unmatched_excel_headers[0]
                                    hint = ""
                                    if u.suggested_matches:
                                        hint = f" Gợi ý: {u.suggested_matches[0].header} ({u.suggested_matches[0].confidence}%)"
                                    st.markdown(f'<span style="color:#ca8a04;font-size:12px;">{len(match_result.unmatched_excel_headers)} cột chưa dùng{hint}</span>',
                                                unsafe_allow_html=True)

                                tpl_name = st.text_input("Lưu mẫu:", key="sp_tpl_name", placeholder="Tên mẫu...", label_visibility="collapsed")
                                c_save, c_confirm = st.columns([1, 1])
                                with c_save:
                                    if st.button("Lưu mẫu", use_container_width=True, key="sp_save_tpl"):
                                        if tpl_name.strip():
                                            save_mapping_template(tpl_name.strip(), dict(current_mapping))
                                            st.success("Đã lưu mẫu")
                                with c_confirm:
                                    if st.button("Xác nhận", type="primary", use_container_width=True, key="sp_confirm"):
                                        st.session_state["mapping_confirmed"] = True

                                if st.session_state.import_step_teachers == 2:
                                    st.markdown("---")
                                    if st.button("Tiếp theo →", key="step2_next_teachers"):
                                        st.session_state.import_step_teachers = 3
                                        st.rerun()

                            with col_right:
                                st.caption("XEM TRƯỚC DỮ LIỆU")
                                try:
                                    import io as _io
                                    df_full = pd.read_excel(_io.BytesIO(file_bytes), sheet_name=selected_sheet,
                                                            header=header_row)
                                    if not df_full.empty:
                                        n = len(df_full)
                                        head = df_full.head(50)
                                        tail = df_full.tail(50)

                                        st.markdown(f'<span style="font-size:12px;color:#6b7280;">50 dòng đầu ({n} dòng)</span>',
                                                    unsafe_allow_html=True)
                                        st.dataframe(head, use_container_width=True, height=200)

                                        st.markdown(f'<span style="font-size:12px;color:#6b7280;">50 dòng cuối</span>',
                                                    unsafe_allow_html=True)
                                        st.dataframe(tail, use_container_width=True, height=200)
                                    else:
                                        st.markdown(f'<span style="font-size:12px;color:#6b7280;">0 dòng — chỉ có tiêu đề cột</span>',
                                                    unsafe_allow_html=True)
                                        st.dataframe(pd.DataFrame(columns=headers), use_container_width=True, height=100)
                                except Exception as _e:
                                    st.caption(f"Không thể đọc dữ liệu xem trước: {_e}")

                            # --- Below the split: validation, diff, submit ---
                            missing_required = [c for c in required_cols if current_mapping.get(c) is None]
                            if missing_required:
                                st.warning(f"⚠️ Vui lòng ghép tất cả các cột bắt buộc: {', '.join(missing_required)}")
                            else:
                                try:
                                    # Read & remap
                                    df_raw = parse_excel_to_df(file_bytes, header_row=header_row, sheet_name=selected_sheet)
                                    df_parsed = remap_dataframe_columns(df_raw, current_mapping)

                                    if df_parsed.empty:
                                        st.info("Không có dòng dữ liệu nào sau khi đọc.")
                                    elif len(df_parsed) > 100000:
                                        st.error("File Excel quá lớn (>100.000 dòng). Vui lòng chia nhỏ file.")
                                    else:
                                        # Validate
                                        errors = validate_teachers_data(df_parsed, get_connection())

                                        if errors:
                                            st.error("❌ Phát hiện lỗi định dạng dữ liệu trong file Excel. Vui lòng sửa lại:")
                                            for idx_e, r_num, err_msg in errors[:20]:
                                                st.write(f"- Dòng {r_num}: {err_msg}")
                                            if len(errors) > 20:
                                                st.caption(f"... và {len(errors) - 20} lỗi khác.")
                                        else:
                                            st.success(f"✓ Dữ liệu hợp lệ! Đã đọc thành công {len(df_parsed)} dòng.")

                                            # Diff
                                            df_diff = diff_teachers(df_parsed, get_connection())

                                            # Filter diff results if not admin
                                            if not is_admin:
                                                df_diff = df_diff[df_diff["Đơn vị"].strip().lower() == dept_name.strip().lower()]

                                            # Diff counts
                                            counts = df_diff["diff_marker"].value_counts().to_dict()
                                            c_new = counts.get("NEW", 0)
                                            c_upd = counts.get("UPDATE", 0)
                                            c_skip = counts.get("SKIP", 0)

                                            cols_m = st.columns(3)
                                            cols_m[0].metric("Thêm mới", c_new)
                                            cols_m[1].metric("Cập nhật / Thay đổi", c_upd)
                                            cols_m[2].metric("Trùng khớp (Bỏ qua)", c_skip)

                                            if st.session_state.import_step_teachers == 3:
                                                if st.button("Tiếp theo →", key="step3_next_teachers"):
                                                    st.session_state.import_step_teachers = 4
                                                    st.rerun()

                                            # Commit to staging database as a pending batch
                                            if st.session_state.import_step_teachers == 4:
                                                if st.button("🚀 Gửi yêu cầu phê duyệt", type="primary", key="btn_submit_teachers_batch", use_container_width=True):
                                                    conn_write = get_connection()
                                                    try:
                                                        cur = conn_write.cursor()
                                                        cur.execute("""
                                                            INSERT INTO import_batches (domain, dept_name, status, uploaded_by, filename, row_count)
                                                            VALUES ('teachers', ?, 'pending', ?, ?, ?)
                                                        """, (dept_name, f"Code {dept_auth_code}", uploaded_teachers.name, len(df_diff)))
                                                        batch_id = cur.lastrowid

                                                        def normalize_date(val):
                                                            if pd.isna(val) or val is None or str(val).strip() == "":
                                                                return None
                                                            try:
                                                                return pd.to_datetime(val).strftime("%Y-%m-%d")
                                                            except Exception:
                                                                return str(val).strip()

                                                        from pipeline.validator import parse_bool
                                                        for idx, row in df_diff.iterrows():
                                                            is_fem = parse_bool(row.get("Nữ"))

                                                            if not is_admin and str(row.get("Đơn vị", "")).strip().lower() != dept_name.strip().lower():
                                                                continue

                                                            role_sdate = normalize_date(row.get("Ngày bổ nhiệm chức vụ"))
                                                            title_sdate = normalize_date(row.get("Ngày bổ nhiệm chức danh"))

                                                            cur.execute("""
                                                                INSERT INTO staging_teachers (
                                                                    batch_id, row_num, diff_marker, diff_detail, validation_errors,
                                                                    teacher_name, subject_group, is_female, employment_type,
                                                                    guest_rank, total_12m_salary, salary_coefficient, title, department, role, teacher_id,
                                                                    role_start_date, title_start_date,
                                                                    study_leave, field_trip, permitted_leave
                                                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                                            """, (
                                                                batch_id, idx + header_row + 2, row["diff_marker"], row["diff_detail"], "",
                                                                row["Họ tên"], row.get("Tổ bộ môn", None), is_fem, row.get("Loại hợp đồng", None),
                                                                row.get("Học hàm học vị") if not pd.isna(row.get("Học hàm học vị")) else None,
                                                                None, None,
                                                                row["Chức danh"] if not pd.isna(row["Chức danh"]) else None,
                                                                row["Đơn vị"],
                                                                row.get("Chức vụ", None) if not pd.isna(row.get("Chức vụ")) else None,
                                                                int(float(str(row["Mã GV"]).strip())) if pd.notna(row.get("Mã GV")) and str(row.get("Mã GV")).strip() and str(row.get("Mã GV")).strip() != "None" else None,
                                                                role_sdate, title_sdate,
                                                                row.get("Thời gian đi học"), row.get("Thời gian đi thực tế"), row.get("Thời gian nghỉ có phép")
                                                            ))
                                                        conn_write.commit()
                                                        st.success("🎉 Đã gửi yêu cầu phê duyệt đến Quản trị viên thành công!")
                                                        st.balloons()
                                                    except Exception as ex:
                                                        st.error(f"Lỗi khi gửi yêu cầu: {ex}")
                                                    finally:
                                                        conn_write.close()
                                except Exception as e_parse:
                                    st.error(f"Không thể đọc file: {e_parse}")

                    except Exception as e_headers:
                        st.error(
                            "⚠️ **Lỗi đọc file Excel:** Không thể phân tích cấu trúc của file Excel được tải lên.\n\n"
                            "**Gợi ý khắc phục:**\n"
                            "- Đảm bảo file không bị lỗi, mật khẩu bảo vệ hoặc bị mã hóa.\n"
                            "- Kiểm tra xem bạn đã chọn đúng tên Sheet và Dòng chứa tiêu đề cột (0-indexed) chưa.\n"
                        )
                        with st.expander("Chi tiết kỹ thuật"):
                            st.code(str(e_headers))


# Close the shared page-level DB connection after all tabs have rendered
conn.close()
