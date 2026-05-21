import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import get_connection, delete_teacher
from components import render_status_bar, render_empty_state, render_warning_state, render_sidebar
from calculations import calculate_t04_weeks, get_timeframe_dates

render_sidebar("canbo")

st.title("Quản lý Hồ sơ Nhà giáo")
st.markdown('<p style="color: var(--md-on-surface-variant); font-size: 16px;">Quản lý thông tin cơ bản và lịch sử công tác (timeline) của nhà giáo.</p>', unsafe_allow_html=True)

conn = get_connection()

with st.expander("Thêm mới Hồ sơ Nhà giáo", expanded=False):
    df_titles = pd.read_sql_query("SELECT name FROM titles", conn)
    titles_list = df_titles['name'].tolist() if not df_titles.empty else ["(Chưa có dữ liệu)"]

    df_depts = pd.read_sql_query("SELECT name FROM departments", conn)
    depts_list = df_depts['name'].tolist() if not df_depts.empty else ["(Chưa có dữ liệu)"]

    df_roles = pd.read_sql_query("SELECT id, name FROM reduction_rules WHERE rule_type = 'ROLE'", conn)
    roles_dict = {row['name']: row['id'] for _, row in df_roles.iterrows()} if not df_roles.empty else {}
    roles_list = ["Không có"] + list(roles_dict.keys())

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
                cursor.execute("INSERT INTO teachers (name, subject_group, is_female) VALUES (?, ?, ?)",
                               (name.strip(), subject_group, int(is_female)))
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

with st.expander("Xóa Hồ sơ (Khu vực Nguy hiểm)"):
    df_all_t = pd.read_sql_query("SELECT id, name FROM teachers", conn)
    if not df_all_t.empty:
        del_opts = {name: int(id) for name, id in zip(df_all_t['name'] + " (ID: " + df_all_t['id'].astype(str) + ")", df_all_t['id'])}
        del_target = st.selectbox("Chọn nhà giáo cần xóa", list(del_opts.keys()), key='del_t_select')
        confirm_delete = st.checkbox("Tôi xác nhận muốn xóa vĩnh viễn dữ liệu của nhà giáo này.")
        if st.button("Xóa toàn bộ dữ liệu của Nhà giáo này", disabled=not confirm_delete):
            delete_teacher(del_opts[del_target])
            st.success("Đã xóa vĩnh viễn dữ liệu!")
            st.rerun()

st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 24px 0;">', unsafe_allow_html=True)

st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">list_alt</span> Danh sách Hồ sơ</h3>', unsafe_allow_html=True)
df_teachers = pd.read_sql_query("SELECT id, name as 'Họ tên', subject_group as 'Khối môn', CASE WHEN is_female=1 THEN 'Nữ' ELSE 'Nam' END as 'Giới tính' FROM teachers", conn)
st.dataframe(df_teachers, width='stretch', hide_index=True)

st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 24px 0;">', unsafe_allow_html=True)

if df_teachers.empty:
    render_warning_state("Vui lòng thêm hồ sơ nhà giáo trước.")
else:
    st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">person_search</span> Chi tiết & Cập nhật Quá trình Công tác</h3>', unsafe_allow_html=True)

    teacher_opts = {name: int(id) for name, id in zip(df_teachers['Họ tên'] + " (ID: " + df_teachers['id'].astype(str) + ")", df_teachers['id'])}
    selected_teacher_name = st.selectbox("Chọn Nhà giáo để xem/cập nhật", options=list(teacher_opts.keys()))
    selected_t_id = teacher_opts[selected_teacher_name]

    current_status_query = """
    SELECT h.record_type, h.value_text, r.name as rule_name, h.id as hist_id, r.rule_type, h.start_date
    FROM teacher_role_history h
    LEFT JOIN reduction_rules r ON h.reduction_rule_id = r.id
    WHERE h.teacher_id = ? AND h.end_date IS NULL
    """
    df_current = pd.read_sql_query(current_status_query, conn, params=[selected_t_id])

    curr_titles = df_current[df_current['record_type'] == 'TITLE']['value_text'].tolist()
    curr_depts = df_current[df_current['record_type'] == 'DEPARTMENT']['value_text'].tolist()
    active_roles = len(df_current[df_current['rule_type'] == 'ROLE'])
    active_events = len(df_current[df_current['rule_type'] == 'SPECIAL'])

    render_status_bar(
        selected_teacher_name.split(' (')[0],
        curr_titles[0] if curr_titles else 'Chưa có',
        curr_depts[0] if curr_depts else 'Chưa có',
        active_roles,
        active_events
    )

    active_reds_query = """
        SELECT h.id, r.name, r.rule_type, h.start_date
        FROM teacher_role_history h
        JOIN reduction_rules r ON h.reduction_rule_id = r.id
        WHERE h.teacher_id = ? AND h.record_type = 'REDUCTION' AND h.end_date IS NULL
    """
    df_active_reds = pd.read_sql_query(active_reds_query, conn, params=[selected_t_id])

    if not df_active_reds.empty:
        cols = st.columns(len(df_active_reds))
        for i, (_, red) in enumerate(df_active_reds.iterrows()):
            with cols[i]:
                badge = "Chức vụ" if red['rule_type'] == 'ROLE' else "Sự kiện"
                variant = "primary" if red['rule_type'] == 'ROLE' else "amber"
                icon = "badge" if red['rule_type'] == 'ROLE' else "event"
                chip_html = f'<span class="md-chip md-chip-{variant}"><span class="material-symbols-outlined" style="font-size: 14px; margin-right: 4px;">{icon}</span>{badge}</span>'
                st.markdown(f"""
<div style="
    background-color: var(--md-surface-container-lowest);
    padding: 16px;
    border-radius: var(--radius-md);
    border: 1px solid var(--md-outline-variant);
    margin-bottom: 8px;
    box-shadow: var(--shadow-card);
">
    <div style="margin-bottom: 8px;">{chip_html}</div>
    <div style="color: var(--md-on-surface); font-weight: 600; font-size: 0.95rem; margin-top: 4px;">{red['name']}</div>
    <div style="color: var(--md-on-surface-variant); font-size: 0.75rem; margin-top: 2px;">Từ {red['start_date']}</div>
</div>
                """, unsafe_allow_html=True)
                if st.button("Kết thúc", key=f"end_red_{red['id']}"):
                    cursor = conn.cursor()
                    cursor.execute("UPDATE teacher_role_history SET end_date = date('now') WHERE id = ?", (red['id'],))
                    conn.commit()
                    st.success("Đã kết thúc!")
                    st.rerun()

    st.markdown("""
<div style="
    background-color: var(--md-primary-fixed);
    padding: 12px 20px;
    border-radius: var(--radius-md);
    border-left: 4px solid var(--md-primary-container);
    color: var(--md-on-primary-fixed);
    margin: 20px 0;
    font-size: 0.9rem;
">
    <span class="material-symbols-outlined" style="font-size: 16px; vertical-align: middle; margin-right: 8px;">lightbulb</span>
    Mẹo: Bấm vào vùng dưới đây để cập nhật chức vụ hoặc xem lịch sử chi tiết.
</div>
    """, unsafe_allow_html=True)

    with st.expander("Cập nhật Biến động & Xem Lịch sử Chi tiết"):

        action = st.selectbox("Chọn thao tác cần thực hiện",
                              ["-- Chọn thao tác --", "Cập nhật Chức danh", "Chuyển Đơn vị", "Thêm Chức vụ Lãnh đạo", "Thêm Sự kiện (Thai sản/Đi học)"])

        def render_change_form(title, form_key, label_col, sql_get_options, field_type):
            st.subheader(title)
            df_opts = pd.read_sql_query(sql_get_options, conn)
            options = df_opts[label_col].tolist() if not df_opts.empty else ["(Chưa có dữ liệu)"]

            opts_dict = {}
            if field_type in ['ROLE', 'SPECIAL']:
                if field_type == 'ROLE':
                    unit_type = st.radio("Chọn phạm vi công tác", ["Tại đơn vị giảng dạy", "Công tác quản lý đảng, đoàn thể hoặc công tác tại phòng, trung tâm"], key=f"unit_type_{form_key}")
                    school_roles = ["Hiệu trưởng", "Phó Hiệu trưởng", "Phó Bí thư Đảng ủy Trường"]
                    if unit_type == "Tại đơn vị giảng dạy":
                        df_opts = df_opts[df_opts['name'].str.contains("Tại đơn vị giảng dạy") | df_opts['name'].isin(["Trưởng khoa", "Phó Trưởng khoa"] + school_roles)]
                    else:
                        df_opts = df_opts[df_opts['name'].str.contains("Công tác quản lý đảng") | df_opts['name'].isin(["Trưởng phòng", "Phó Trưởng phòng", "Công tác tại phòng, trung tâm không giữ chức vụ lãnh đạo"] + school_roles)]

                opts_dict = {f"{row['name']}": row['id'] for _, row in df_opts.iterrows()}
                options = list(opts_dict.keys()) if opts_dict else ["(Chưa có dữ liệu)"]

            selected_val = st.selectbox("Chọn giá trị mới", options=options, key=f"val_{form_key}")

            start_date_inner = st.date_input("Ngày bắt đầu hiệu lực", key=f"start_{form_key}")
            is_ongoing = True
            if field_type in ['ROLE', 'SPECIAL']:
                is_ongoing = st.checkbox("Đang diễn ra", value=True, key=f"ongoing_{form_key}")
            end_date_inner = st.date_input("Ngày kết thúc", disabled=is_ongoing, key=f"end_{form_key}")

            weeks_override = None
            if field_type in ['ROLE', 'SPECIAL']:
                tf_id, tf_start, tf_end, _ = get_timeframe_dates(conn)
                tf_start_date = tf_start.date() if tf_start is not None else None
                tf_end_date = tf_end.date() if tf_end is not None else None

                if tf_id:
                    df_holidays = pd.read_sql_query("SELECT start_date, end_date FROM academic_holidays WHERE timeframe_id = ?", conn, params=[tf_id])
                else:
                    df_holidays = pd.DataFrame(columns=['start_date', 'end_date'])
                holidays_list = [(pd.to_datetime(h['start_date']), pd.to_datetime(h['end_date'])) for _, h in df_holidays.iterrows()]

                if not is_ongoing:
                    if end_date_inner < start_date_inner:
                        st.error("Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu!")
                    else:
                        cal_days = (end_date_inner - start_date_inner).days + 1
                        raw_weeks = round(cal_days / 7.0, 1)
                        calc_weeks = calculate_t04_weeks(start_date_inner, end_date_inner, holidays_list)

                        clipped_weeks = calc_weeks
                        is_clipped = False
                        if tf_start_date is not None and tf_end_date is not None:
                            if start_date_inner < tf_start_date or end_date_inner > tf_end_date:
                                clip_start = max(start_date_inner, tf_start_date)
                                clip_end = min(end_date_inner, tf_end_date)
                                if clip_start <= clip_end:
                                    clipped_weeks = calculate_t04_weeks(clip_start, clip_end, holidays_list)
                                else:
                                    clipped_weeks = 0.0

                                if clipped_weeks < calc_weeks:
                                    is_clipped = True
                                    remaining_weeks = calc_weeks - clipped_weeks
                                    st.warning(
                                        f"**Lưu ý (Cắt khung năm học):** Hoạt động này kéo dài ngoài khung năm học hiện tại "
                                        f"({tf_start_date.strftime('%d/%m/%Y')} - {tf_end_date.strftime('%d/%m/%Y')}). "
                                        f"Hệ thống tự động cắt thời gian và chỉ tính **{clipped_weeks:.1f} tuần** cho năm học này. "
                                        f"Phần còn lại ({remaining_weeks:.1f} tuần) sẽ chuyển sang năm học kế tiếp."
                                    )

                        if not is_clipped:
                            if abs(calc_weeks - raw_weeks) >= 0.1:
                                st.info(
                                    f"Tính toán tự động: **{calc_weeks:.1f} tuần** "
                                    f"(giảm từ {raw_weeks:.1f} tuần lịch do trùng điều chỉnh)."
                                )
                            else:
                                st.info(f"Tính toán tự động: **{calc_weeks:.1f} tuần**.")
                else:
                    st.info("Tính toán tự động: Hoạt động đang diễn ra (tính đến cuối khung năm học).")

                with st.expander("Chỉnh sửa số tuần thực tế (Nâng cao/Ghi đè)"):
                    st.markdown("*Sử dụng tính năng này khi cần khớp chính xác với số tuần trên văn bản quyết định hoặc muốn tính trọn vẹn số tuần mà không bị cắt theo khung năm học.*")
                    use_override = st.checkbox("Kích hoạt ghi đè số tuần", value=False, key=f"override_check_{form_key}")
                    if use_override:
                        default_val = 44.0
                        if not is_ongoing and 'calc_weeks' in locals():
                            default_val = float(calc_weeks)
                        weeks_override = st.number_input(
                            "Số tuần thực tế ghi đè",
                            min_value=0.0,
                            max_value=52.0,
                            value=default_val,
                            step=0.5,
                            key=f"override_val_{form_key}"
                        )
                        st.info(f"Đang ghi đè: Áp dụng **{weeks_override:.1f} tuần** thay vì tính tự động.")

            if st.button("Lưu", key=f"submit_{form_key}"):
                if not options or options[0] == "(Chưa có dữ liệu)":
                    st.error("Vui lòng cài đặt danh mục trước.")
                else:
                    if field_type in ['TITLE', 'DEPARTMENT']:
                        active_rec = df_current[df_current['record_type'] == field_type]
                    else:
                        active_rec = df_current[df_current['rule_type'] == field_type]

                    if not active_rec.empty and active_rec.iloc[0]['start_date']:
                        try:
                            current_start = datetime.strptime(active_rec.iloc[0]['start_date'], '%Y-%m-%d').date()
                            if start_date_inner <= current_start:
                                st.error(f"Ngày bắt đầu mới phải sau ngày bắt đầu của bản ghi hiện tại ({current_start})!")
                                return
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
                    st.success("Đã cập nhật!")
                    st.rerun()

        if action == "Cập nhật Chức danh":
            render_change_form("Cập nhật Chức danh", "f_title", "name", "SELECT name FROM titles", "TITLE")
        elif action == "Chuyển Đơn vị":
            render_change_form("Chuyển Đơn vị", "f_dept", "name", "SELECT name FROM departments", "DEPARTMENT")
        elif action == "Thêm Chức vụ Lãnh đạo":
            render_change_form("Thêm Chức vụ Lãnh đạo", "f_role", "name", "SELECT id, name FROM reduction_rules WHERE rule_type = 'ROLE'", "ROLE")
        elif action == "Thêm Sự kiện (Thai sản/Đi học)":
            render_change_form("Thêm Sự kiện (Thai sản/Đi học)", "f_event", "name", "SELECT id, name FROM reduction_rules WHERE rule_type = 'SPECIAL'", "SPECIAL")

        st.markdown(f'<hr style="border-color: var(--md-outline-variant); margin: 24px 0;">', unsafe_allow_html=True)

        st.markdown('<h3 style="display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="color: var(--md-primary-container);">history</span> Bảng Lịch sử Chi tiết</h3>', unsafe_allow_html=True)

        view_mode = st.radio("Chế độ xem:", ["Tất cả", "Nhân sự (Chức danh/Đơn vị)", "Miễn giảm & Chức vụ"], horizontal=True)

        query = """
            SELECT
                h.id as 'ID',
                CASE
                    WHEN h.record_type = 'TITLE' THEN 'Chức danh'
                    WHEN h.record_type = 'DEPARTMENT' THEN 'Đơn vị'
                    WHEN r.rule_type = 'ROLE' THEN 'Chức vụ'
                    ELSE 'Sự kiện'
                END as 'Loại',
                COALESCE(h.value_text, r.name) as 'Chi tiết',
                h.start_date as 'Từ ngày',
                COALESCE(h.end_date, 'Đến nay') as 'Đến ngày',
                COALESCE(CAST(h.actual_weeks_override AS TEXT), 'Tự động') as 'Số tuần thực tế'
            FROM teacher_role_history h
            LEFT JOIN reduction_rules r ON h.reduction_rule_id = r.id
            WHERE h.teacher_id = ?
        """

        if view_mode == "Nhân sự (Chức danh/Đơn vị)":
            query += " AND h.record_type IN ('TITLE', 'DEPARTMENT')"
        elif view_mode == "Miễn giảm & Chức vụ":
            query += " AND h.record_type = 'REDUCTION'"

        query += " ORDER BY h.start_date DESC"

        hist_df = pd.read_sql_query(query, conn, params=[selected_t_id])

        if not hist_df.empty:
            st.dataframe(hist_df, width='stretch', hide_index=True)
        else:
            st.info("Chưa có dữ liệu lịch sử.")

        with st.expander("Quản lý dòng lịch sử (Xóa lỗi)"):
            df_all_hist = pd.read_sql_query("""
                SELECT h.id, h.record_type, COALESCE(h.value_text, r.name) as detail
                FROM teacher_role_history h
                LEFT JOIN reduction_rules r ON h.reduction_rule_id = r.id
                WHERE h.teacher_id = ?
            """, conn, params=[selected_t_id])

            if not df_all_hist.empty:
                del_opts = {f"ID {row['id']}: {row['record_type']} - {row['detail']}": row['id'] for _, row in df_all_hist.iterrows()}
                selected_del = st.selectbox("Chọn dòng cần xóa", options=list(del_opts.keys()))
                del_id = del_opts[selected_del]

                if st.button("Xoá mục này", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM teacher_role_history WHERE id = ?", (del_id,))
                    conn.commit()
                    st.success("Đã xoá!")
                    st.rerun()
            else:
                st.info("Không có dữ liệu để quản lý.")

conn.close()
