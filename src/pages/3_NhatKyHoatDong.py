import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import streamlit as st
from datetime import date
from database import (
    get_connection,
    get_cached_teachers,
    get_cached_activity_types,
    get_cached_timeframes,
    ThreadLocalConnectionProxy,
)
from components import render_empty_state, render_warning_state, render_sidebar
from auth import get_current_user, get_scoped_teacher_ids, require_role

require_role(["admin", "head_dept"], "Ghi nhận Hoạt động")


def _load_sample_data(file_bytes, sheet_name, header_row, headers):
    try:
        import io as _io
        import pandas as pd

        df = pd.read_excel(
            _io.BytesIO(file_bytes), sheet_name=sheet_name, header=header_row, nrows=1
        )
        if df.empty:
            return {}
        return {h: df.iloc[0].get(h, "") for h in headers}
    except Exception:
        return {}


st.set_page_config(page_title="Ghi nhận Hoạt động", page_icon="📝", layout="wide")
render_sidebar("nhatky")

st.title("📝 Ghi nhận Hoạt động")
st.markdown(
    '<p style="color: var(--md-on-surface-variant); font-size: 16px;">Nhập liệu các hoạt động giảng dạy, NCKH và nhiệm vụ khác.</p>',
    unsafe_allow_html=True,
)

conn = ThreadLocalConnectionProxy()

user = get_current_user()
scoped_ids = get_scoped_teacher_ids(user)

df_teachers = get_cached_teachers()
if scoped_ids is not None:
    df_teachers = df_teachers[df_teachers["id"].isin(scoped_ids)]

df_activities = get_cached_activity_types()
df_timeframes = get_cached_timeframes()

if df_teachers.empty or df_activities.empty or df_timeframes.empty:
    render_warning_state(
        "Cần thêm Nhà giáo, cấu hình Loại hoạt động và Năm học trước khi ghi nhận nhật ký."
    )
    conn.close()
else:
    teacher_options = {
        f"{row['name']} ({row['subject_group']})": int(row["id"])
        for idx, row in df_teachers.iterrows()
    }
    tf_options = {row["name"]: int(row["id"]) for idx, row in df_timeframes.iterrows()}

    if user is None:
        (tab_list,) = st.tabs(["📋 Lịch sử Hoạt động (Gần đây)"])
    else:
        tab_list, tab_new, tab_bulk = st.tabs(
            [
                "📋 Lịch sử Hoạt động (Gần đây)",
                "➕ Ghi nhận mới",
                "📥 Nhập hàng loạt từ Excel",
            ]
        )

    with tab_list:
        query = """
        SELECT al.id, t.name as 'Nhà giáo', at.name as 'Hoạt động', tf.name as 'Timeframe',
               al.log_date as 'Ngày', al.quantity as 'Số lượng', al.class_level as 'Cấp/Lớp',
               al.class_type, al.student_count as 'Sĩ số', al.note as 'Ghi chú',
               at.category, at.base_conversion_rate, at.is_teaching_activity, at.is_nckh_activity,
               al.timeframe_id, al.teacher_id
        FROM activity_logs al
        JOIN teachers t ON al.teacher_id = t.id
        JOIN activity_types at ON al.activity_type_id = at.id
        JOIN timeframes tf ON al.timeframe_id = tf.id
        ORDER BY al.log_date DESC, al.id DESC
        LIMIT 100
        """

        from calculations import calculate_activity_hours
        import pandas as pd

        df_logs = pd.read_sql_query(query, conn)
        if scoped_ids is not None:
            df_logs = df_logs[df_logs["teacher_id"].isin(scoped_ids)]

        if not df_logs.empty:
            hours_list = []
            for idx, row in df_logs.iterrows():
                hours = calculate_activity_hours(
                    row.rename(
                        {
                            "Số lượng": "quantity",
                            "Cấp/Lớp": "class_level",
                            "Sĩ số": "student_count",
                        }
                    ),
                    row,
                )
                hours_list.append(hours)
            df_logs["Giờ chuẩn (Ước tính)"] = hours_list

            display_cols = [
                "id",
                "Nhà giáo",
                "Hoạt động",
                "Ngày",
                "Số lượng",
                "Cấp/Lớp",
                "Sĩ số",
                "Giờ chuẩn (Ước tính)",
                "Ghi chú",
            ]
            df_display = df_logs[[c for c in display_cols if c in df_logs.columns]]
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            if user is not None:
                st.markdown("### 🗑️ Xoá Nhật ký")
                col_del = st.columns([2, 3])
                with col_del[0]:
                    del_id = st.selectbox(
                        "Chọn dòng nhật ký cần xoá:",
                        options=df_logs["id"].tolist(),
                        format_func=lambda x: (
                            f"Dòng #{x}: {df_logs[df_logs['id'] == x]['Nhà giáo'].values[0]} - {df_logs[df_logs['id'] == x]['Hoạt động'].values[0]} ({df_logs[df_logs['id'] == x]['Timeframe'].values[0]})"
                        ),
                    )

                selected_log_row = df_logs[df_logs["id"] == del_id].iloc[0]
                log_tf_id = int(selected_log_row["timeframe_id"])

                # Check if timeframe is locked by Excel data
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM session_teacher_totals WHERE timeframe_id = ?",
                    (log_tf_id,),
                )
                log_tf_locked = cursor.fetchone()[0] > 0

                if log_tf_locked:
                    st.warning(
                        "⚠️ Không thể xoá dòng nhật ký này vì năm học tương ứng đã được khóa để quản lý qua Excel."
                    )
                else:
                    confirm_key = f"confirm_del_log_{del_id}"
                    if st.session_state.get(confirm_key, False):
                        st.warning(
                            f"⚠️ Bạn có chắc chắn muốn xóa dòng nhật ký #{del_id} này không?"
                        )
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button(
                                "Xác nhận xóa vĩnh viễn",
                                key=f"yes_log_{del_id}",
                                type="primary",
                            ):
                                cursor = conn.cursor()
                                cursor.execute(
                                    "DELETE FROM activity_logs WHERE id = ?",
                                    (int(del_id),),
                                )
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

    if user is None:
        conn.close()
        st.stop()

    with tab_new:
        col_left, col_right = st.columns(2)
        teacher_sel = col_left.selectbox(
            "Chọn Nhà giáo", options=list(teacher_options.keys())
        )
        selected_teacher_id = teacher_options[teacher_sel]
        selected_emp_type = df_teachers[df_teachers["id"] == selected_teacher_id].iloc[
            0
        ]["employment_type"]

        def _row_applies(r, emp_type):
            import pandas as pd

            val = r.get("applicable_employment_types", "ALL")
            if pd.isna(val) or val == "ALL":
                return True
            return emp_type in str(val).split(",")

        act_mask = df_activities.apply(
            lambda r: _row_applies(r, selected_emp_type), axis=1
        )
        df_filtered = df_activities[act_mask]
        activity_options = {
            f"[{row['category']}] {row['name']}": int(row["id"])
            for idx, row in df_filtered.iterrows()
        }
        activity_sel = col_right.selectbox(
            "Chọn Hoạt động", options=list(activity_options.keys())
        )
        selected_act_id = activity_options[activity_sel]
        act_info = df_activities[df_activities["id"] == selected_act_id].iloc[0]
        unit = act_info["unit"]

        col3, col4 = st.columns(2)
        log_date = col3.date_input("Ngày thực hiện", value=date.today())

        global_tf_id = st.session_state.get("global_tf_id")
        global_tf_name = next(
            (k for k, v in tf_options.items() if v == global_tf_id), "Năm học"
        )

        col4.markdown(
            f'<div style="padding-top: 10px;"><label style="font-size: 14px; font-weight: 600; color: var(--md-on-surface-variant);">Năm học (Toàn cục)</label><div style="font-size: 16px; font-weight: 700; color: var(--md-primary); margin-top: 8px;">📅 {global_tf_name}</div></div>',
            unsafe_allow_html=True,
        )

        final_tf_id = global_tf_id

        # Check lock state for the selected target timeframe
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM session_teacher_totals WHERE timeframe_id = ?",
            (final_tf_id,),
        )
        is_tf_locked = cursor.fetchone()[0] > 0

        if is_tf_locked:
            st.warning(
                f"⚠️ Năm học **{global_tf_name}** đã được khóa nhập lẻ để quản lý tập trung bằng Excel. Vui lòng chọn năm học khác hoặc xóa file Excel tại trang Nhập dữ liệu để mở khóa."
            )

        with st.form("log_activity_form"):
            is_freeform = act_info["category"] == "Chấp hành Nhiệm vụ khác"

            if is_freeform:
                freeform_desc = st.text_area(
                    "Mô tả nhiệm vụ",
                    placeholder="Ví dụ: Tham gia hội thảo an ninh, họp chuyên môn đột xuất,...",
                )
                total_hours = st.number_input(
                    "Tổng số giờ thực hiện",
                    min_value=0.0,
                    value=1.0,
                    step=0.5,
                    help="Nhập trực tiếp tổng số giờ đã thực hiện (không qua quy đổi)",
                )
                st.info(
                    "Hoạt động này không tính vào giờ chuẩn giảng dạy (GC) — chỉ mang tính thống kê."
                )
                quantity = total_hours
            else:
                col_qty, _ = st.columns([1, 1])
                quantity = col_qty.number_input(
                    f"Số lượng gốc ({unit})", min_value=0.0, value=1.0, step=0.5
                )

            class_level = (
                "Đại học"
                if act_info["is_teaching_activity"] and not is_freeform
                else None
            )
            class_type = (
                "Lý thuyết"
                if act_info["is_teaching_activity"] and not is_freeform
                else None
            )
            student_count = (
                40 if act_info["is_teaching_activity"] and not is_freeform else 0
            )
            nckh_level = None
            is_main_author = False
            is_foreign_instruction = False

            if act_info["is_teaching_activity"] and not is_freeform:
                st.info(
                    "💡 Hệ thống mặc định hệ số lớp: Đại học, Lý thuyết, 40 SV. Chỉ thay đổi dưới đây nếu cần."
                )
                with st.expander("📐 Chi tiết Lớp học (để tính hệ số)", expanded=False):
                    col_a_c, col_b_c, col_c_c = st.columns(3)
                    class_level = col_a_c.selectbox(
                        "Cấp học",
                        [
                            "Đại học",
                            "Thạc sĩ",
                            "Tiến sĩ",
                            "LLCT Trung cấp",
                            "LLCT Cao cấp",
                            "Bồi dưỡng",
                        ],
                        index=0,
                    )
                    class_type = col_b_c.selectbox(
                        "Loại hình",
                        [
                            "Lý thuyết",
                            "Thực hành",
                            "Ngoại ngữ/CNTT",
                            "Thảo luận",
                            "Bài tập",
                            "Xêmina",
                        ],
                        index=0,
                    )
                    student_count = col_c_c.number_input(
                        "Sĩ số (quyết định hệ số nhân)",
                        min_value=1,
                        max_value=200,
                        value=40,
                    )
                    is_foreign_instruction = st.checkbox(
                        "Giảng dạy bằng tiếng nước ngoài", value=False
                    )

            elif act_info["is_nckh_activity"]:
                st.markdown(
                    """
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
                """,
                    unsafe_allow_html=True,
                )
                if act_info["category"] == "NCKH - Hướng dẫn thi đấu":
                    rate = act_info["base_conversion_rate"]
                    st.info(
                        f"Hoạt động này được tính cố định **{rate}h** chuẩn NCKH theo quy định."
                    )
                else:
                    nckh_level_opts = ["Quốc gia", "Bộ/Tỉnh", "Cơ sở", "Trường"]
                    nckh_role_map = {
                        "Chủ nhiệm / Tác giả chính": True,
                        "Thành viên tham gia": False,
                    }
                    col_level, col_role = st.columns(2)
                    with col_level:
                        nckh_level = st.selectbox(
                            "Cấp đề tài", nckh_level_opts, key="nckh_level"
                        )
                    with col_role:
                        role_label = st.selectbox(
                            "Vai trò", list(nckh_role_map.keys()), key="nckh_role"
                        )
                        is_main_author = nckh_role_map[role_label]

            if is_freeform:
                note = freeform_desc
            else:
                note = st.text_input("Ghi chú chi tiết")

            submit = st.form_submit_button("Lưu nhật ký", disabled=is_tf_locked)

            if submit and not is_tf_locked:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO activity_logs (
                        teacher_id, activity_type_id, log_date, quantity,
                        class_level, class_type, student_count, nckh_level, is_main_author,
                        is_foreign_language_instruction, converted_hours, note, timeframe_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        teacher_options[teacher_sel],
                        selected_act_id,
                        log_date,
                        quantity,
                        class_level,
                        class_type,
                        student_count,
                        nckh_level,
                        int(is_main_author),
                        int(is_foreign_instruction),
                        0.0,
                        note,
                        final_tf_id,
                    ),
                )
                conn.commit()
                st.success("Đã lưu nhật ký thành công!")
                from calculations import calculate_activity_hours

                try:
                    preview = calculate_activity_hours(
                        {
                            "quantity": quantity,
                            "class_level": class_level,
                            "class_type": class_type,
                            "student_count": student_count,
                            "nckh_level": nckh_level,
                            "is_main_author": is_main_author,
                            "is_foreign_language_instruction": is_foreign_instruction,
                        },
                        act_info,
                    )
                    st.markdown(
                        f'<div style="background:var(--md-green-bg);padding:8px 12px;border-radius:var(--radius-md);font-size:13px;">'
                        f"<b>Giờ chuẩn ước tính:</b> {preview:.2f}h &nbsp;|&nbsp; "
                        f'<span style="color:var(--md-on-surface-variant);">Số lượng: {quantity} × Hệ số: {act_info.get("base_conversion_rate", 1.0)} × Hệ số lớp</span></div>',
                        unsafe_allow_html=True,
                    )
                except Exception:
                    pass
                st.rerun()

    with tab_bulk:
        st.markdown("### 📥 Nhập nhật ký hoạt động hàng loạt từ Excel")
        st.markdown("""
        Hướng dẫn:
        1. Nhập **Mã bảo mật Khoa/Bộ môn** của bạn để xác thực đơn vị.
        2. Chọn **Năm học** áp dụng.
        3. Tải file mẫu Excel và điền thông tin hoạt động của các cán bộ.
        4. Tải lên file đã điền và bấm **Gửi yêu cầu phê duyệt**.
        """)

        col_code, col_tf = st.columns(2)
        with col_code:
            dept_auth_code = st.text_input(
                "Nhập mã bảo mật Khoa/Bộ môn:",
                type="password",
                key="dept_auth_code_activities",
            )
        with col_tf:
            global_tf_id = st.session_state.get("global_tf_id")
            global_tf_name = next(
                (k for k, v in tf_options.items() if v == global_tf_id), "Năm học"
            )
            st.markdown(
                f'<div style="padding-top: 10px;"><label style="font-size: 14px; font-weight: 600; color: var(--md-on-surface-variant);">Năm học (Toàn cục)</label><div style="font-size: 16px; font-weight: 700; color: var(--md-primary); margin-top: 8px;">📅 {global_tf_name}</div></div>',
                unsafe_allow_html=True,
            )
            selected_tf_name = global_tf_name

        if dept_auth_code:
            from auth import get_department_by_code

            dept_info = get_department_by_code(dept_auth_code)
            if not dept_info:
                st.error("Mã bảo mật Khoa/Bộ môn không chính xác.")
            else:
                dept_id, dept_name = dept_info
                st.success(f"✓ Đã xác thực đơn vị: **{dept_name}**")

                # Selection of import method
                st.markdown("##### ⚙️ Phương thức nhập dữ liệu:")
                import_method = st.radio(
                    "Phương thức nhập dữ liệu:",
                    options=["activities", "aggregate_totals"],
                    format_func=lambda x: (
                        "📝 Nhập chi tiết từng hoạt động (Khuyên dùng)"
                        if x == "activities"
                        else "⚡ Nhập tổng số Giờ chuẩn tích lũy (Ghi đè trực tiếp)"
                    ),
                    key="import_method_radio_choice",
                    label_visibility="collapsed",
                )

                if import_method == "activities":
                    st.info(
                        "💡 **Chế độ Nhập chi tiết:** Bạn sẽ tải lên bảng Excel liệt kê từng công việc cụ thể (VD: Dạy lớp A, Nghiên cứu đề tài B). Hệ thống sẽ tự động đối chiếu định mức, áp dụng các quy tắc quy đổi và tự động tính toán số Giờ chuẩn (GC) cho từng dòng."
                    )
                else:
                    st.warning(
                        "⚠️ **Chế độ Ghi đè tổng số:** Bạn sẽ tải lên bảng tổng hợp ĐÃ CÓ SẴN con số tổng GC của từng cán bộ. Dữ liệu này sẽ **ghi đè trực tiếp** lên hệ thống mà không qua tính toán quy đổi. Chỉ nên dùng khi bạn đã chốt số liệu thủ công từ trước."
                    )

                # ── Stepper navigation ──
                stepper_steps = ["Tải lên", "Ghép cột", "Kiểm tra & Gửi"]
                if "import_step" not in st.session_state:
                    st.session_state.import_step = 1

                step_html = '<div style="display:flex;gap:4px;margin:16px 0;padding:8px 0;border-top:1px solid var(--md-outline-variant);border-bottom:1px solid var(--md-outline-variant);">'
                for i, label in enumerate(stepper_steps):
                    sn = i + 1
                    is_active = sn == st.session_state.import_step
                    is_done = sn < st.session_state.import_step
                    bg = (
                        "var(--md-primary)"
                        if is_active
                        else "var(--md-primary-container)"
                        if is_done
                        else "var(--md-surface-dim)"
                    )
                    c = (
                        "#fff"
                        if is_active
                        else "var(--md-primary)"
                        if is_done
                        else "var(--md-on-surface-variant)"
                    )
                    check = "✓ " if is_done else ""
                    step_html += f'<div style="flex:1;text-align:center;padding:6px 4px;border-radius:var(--radius-md);background:{bg};border:1px solid var(--md-outline-variant);">'
                    step_html += f'<span style="font-size:12px;font-weight:600;color:{c};">{check}{label}</span></div>'
                step_html += "</div>"
                st.markdown(step_html, unsafe_allow_html=True)

                if st.session_state.import_step == 1:
                    # Button to download template
                    from pipeline.templates import generate_activities_template

                    try:
                        template_bytes = generate_activities_template(
                            dept_name, selected_tf_name
                        )
                        st.download_button(
                            label=f"📥 Tải file mẫu Excel Nhật ký Hoạt động ({dept_name} - {selected_tf_name})",
                            data=template_bytes,
                            file_name=f"Mau_Nhat_Ky_Hoat_Dong_{dept_name.replace(' ', '_')}_{selected_tf_name.replace(' ', '_')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_activities_template_btn",
                        )
                    except Exception as e:
                        st.error(f"Lỗi tạo file mẫu: {e}")

                if st.session_state.import_step >= 1:
                    st.info(
                        "💡 **Mẹo:** Bạn có thể tải lên bất kỳ bảng Excel nào từ các hệ thống khác. Hệ thống hỗ trợ tính năng tự động nhận diện tiêu đề cột thông minh."
                    )

                st.markdown("---")
                st.markdown("##### Tải lên file Excel dữ liệu:")
                uploaded_file = st.file_uploader(
                    "Chọn file Excel chứa dữ liệu:",
                    type=["xlsx", "xls"],
                    label_visibility="collapsed",
                    key="uploaded_import_file_excel",
                )

                if uploaded_file is not None:
                    if uploaded_file.size > 5 * 1024 * 1024:
                        st.error(
                            "❌ File tải lên vượt quá giới hạn dung lượng cho phép (5MB). Vui lòng thử lại với file nhỏ hơn."
                        )
                    else:
                        file_bytes = uploaded_file.read()

                        if st.session_state.import_step == 1:
                            st.success(
                                "✅ Đã tải file lên thành công. Vui lòng nhấn **Tiếp theo** để chuyển sang bước Ghép cột."
                            )
                            if st.button("Tiếp theo →", key="step1_next_after_upload"):
                                st.session_state.import_step = 2
                                st.rerun()

                        if st.session_state.import_step >= 2:
                            from pipeline.importer import (
                                parse_excel_to_df,
                                get_excel_sheet_names,
                                get_excel_headers,
                                remap_dataframe_columns,
                            )
                            from pipeline.fuzzy_matcher import match_columns
                            from pipeline.validator import (
                                validate_activities_data,
                                validate_aggregate_totals_data,
                            )
                            from pipeline.differ import (
                                diff_activities,
                                diff_aggregate_totals,
                            )

                            try:
                                sheet_names = get_excel_sheet_names(file_bytes)
                                col_sh, col_hd = st.columns(2)
                                with col_sh:
                                    selected_sheet = st.selectbox(
                                        "Chọn Sheet cần đọc:",
                                        options=sheet_names,
                                        key="import_selected_sheet_sel",
                                    )
                                with col_hd:
                                    header_row = st.number_input(
                                        "Dòng chứa tiêu đề (0-indexed):",
                                        min_value=0,
                                        max_value=20,
                                        value=3 if import_method == "activities" else 0,
                                        step=1,
                                        key="import_header_row_val",
                                    )

                                headers = get_excel_headers(
                                    file_bytes,
                                    sheet_name=selected_sheet,
                                    header_row=header_row,
                                )
                                if not headers:
                                    st.error(
                                        "Không tìm thấy tiêu đề cột nào tại dòng đã chọn."
                                    )
                                else:
                                    conditional_cols = []
                                    if import_method == "activities":
                                        is_teaching_sheet = any(
                                            k in selected_sheet.lower()
                                            for k in ["chuyên môn", "giảng dạy"]
                                        )
                                        is_nckh_sheet = any(
                                            k in selected_sheet.lower()
                                            for k in ["nckh", "nghiên cứu"]
                                        )

                                        required_cols = [
                                            "Mã GV",
                                            "Tên loại hoạt động",
                                            "Ngày thực hiện",
                                            "Số lượng",
                                        ]

                                        if is_teaching_sheet:
                                            required_cols.extend(
                                                ["Cấp lớp", "Loại lớp", "Số học viên"]
                                            )
                                            optional_cols = [
                                                "Cấp đề tài",
                                                "Tác giả chính",
                                                "Giảng dạy tiếng nước ngoài",
                                                "Ghi chú",
                                            ]
                                        elif is_nckh_sheet:
                                            required_cols.extend(["Cấp đề tài"])
                                            optional_cols = [
                                                "Cấp lớp",
                                                "Loại lớp",
                                                "Số học viên",
                                                "Tác giả chính",
                                                "Giảng dạy tiếng nước ngoài",
                                                "Ghi chú",
                                            ]
                                        else:
                                            conditional_cols = [
                                                "Cấp lớp",
                                                "Loại lớp",
                                                "Số học viên",
                                                "Cấp đề tài",
                                            ]
                                            optional_cols = [
                                                "Tác giả chính",
                                                "Giảng dạy tiếng nước ngoài",
                                                "Ghi chú",
                                            ]
                                    else:
                                        required_cols = [
                                            "Mã GV",
                                            "Tổng GC thực hiện",
                                            "NCKH thực hiện",
                                            "Số giờ miễn giảm",
                                            "Định mức GC",
                                        ]
                                        optional_cols = ["Ghi chú"]

                                    all_target_cols = (
                                        required_cols + conditional_cols + optional_cols
                                    )

                                    # Mapping templates management
                                    from pipeline.mapping_templates import (
                                        load_mapping_templates,
                                        save_mapping_template,
                                        delete_mapping_template,
                                    )

                                    saved_templates = load_mapping_templates()
                                    template_options = [
                                        "(Chọn cấu hình đã lưu)"
                                    ] + list(saved_templates.keys())

                                    col_tpl_sel, col_tpl_del = st.columns([3, 1])
                                    with col_tpl_sel:
                                        selected_tpl = st.selectbox(
                                            "Sử dụng cấu hình cột đã lưu:",
                                            options=template_options,
                                            key="selected_mapping_template_name",
                                        )
                                    with col_tpl_del:
                                        st.write("")
                                        st.write("")
                                        if selected_tpl != "(Chọn cấu hình đã lưu)":
                                            if st.button(
                                                "🗑️ Xóa cấu hình này",
                                                key="delete_tpl_btn",
                                            ):
                                                delete_mapping_template(selected_tpl)
                                                st.success(
                                                    f"Đã xóa cấu hình '{selected_tpl}'"
                                                )
                                                st.rerun()

                                    # Retrieve defaults with structured result
                                    if selected_tpl != "(Chọn cấu hình đã lưu)":
                                        defaults = saved_templates[selected_tpl]
                                        match_result = None
                                    else:
                                        match_result = match_columns(
                                            headers,
                                            all_target_cols,
                                            required_columns=required_cols,
                                            return_format="structured",
                                        )
                                        defaults = match_result.to_legacy_dict()

                                    # --- Initialize session mapping ---
                                    mapping_key = f"_excel_mapping_{hash(file_bytes)}_{selected_tpl}_{import_method}"
                                    if mapping_key not in st.session_state:
                                        st.session_state[mapping_key] = dict(defaults)
                                    current_mapping = st.session_state[mapping_key]

                                    # --- Load sample data once ---
                                    sample_key = f"_sample_data_{hash(file_bytes)}_{selected_sheet}_{header_row}"
                                    if sample_key not in st.session_state:
                                        st.session_state[sample_key] = (
                                            _load_sample_data(
                                                file_bytes,
                                                selected_sheet,
                                                header_row,
                                                headers,
                                            )
                                        )

                                    # --- Split panel: mapping + data preview ---
                                    st.markdown(
                                        """<style>
                                    .sp-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; display:inline-block; vertical-align:middle; margin-right:6px; }
                                    .sp-dot.g { background:#22c55e; }
                                    .sp-dot.y { background:#eab308; }
                                    .sp-dot.r { background:#ef4444; }
                                    .sp-badge { background:#ef4444; color:#fff; font-size:9px; padding:1px 5px; border-radius:3px; margin-left:4px; font-weight:600; white-space:nowrap; }
                                    .sp-preview { border-left:1px solid #e5e7eb; padding-left:16px; }
                                    </style>""",
                                        unsafe_allow_html=True,
                                    )

                                    if st.session_state.import_step == 2:
                                        col_left, col_right = st.columns([0.4, 0.6])
                                        with col_left:
                                            st.caption("GHÉP CỘT DỮ LIỆU")
                                            st.markdown(
                                                "Vui lòng ghép các cột từ file Excel của bạn tương ứng với các trường dữ liệu hệ thống yêu cầu."
                                            )
                                            col_map = {
                                                m.expected_column: m
                                                for m in (
                                                    match_result.mappings
                                                    if match_result
                                                    else []
                                                )
                                            }
                                            req_cols_list = required_cols
                                            opt_cols_list = optional_cols

                                            for col in req_cols_list:
                                                m = col_map.get(col)
                                                val = current_mapping.get(col)
                                                is_missing = val is None
                                                dot = (
                                                    "r"
                                                    if is_missing
                                                    else (
                                                        "g"
                                                        if m and m.confidence >= 90
                                                        else "y"
                                                    )
                                                )

                                                rc = st.columns([0.3, 1.5, 2.8])
                                                with rc[0]:
                                                    st.markdown(
                                                        f'<span class="sp-dot {dot}"></span>',
                                                        unsafe_allow_html=True,
                                                    )
                                                with rc[1]:
                                                    st.markdown(
                                                        f'<span style="font-size:13px;font-weight:500;">{col}<span class="sp-badge">BẮT BUỘC</span></span>',
                                                        unsafe_allow_html=True,
                                                    )
                                                with rc[2]:
                                                    di = 0
                                                    cur = current_mapping.get(col)
                                                    if cur in headers:
                                                        di = headers.index(cur) + 1
                                                    elif (
                                                        m
                                                        and m.matched_header in headers
                                                    ):
                                                        di = (
                                                            headers.index(
                                                                m.matched_header
                                                            )
                                                            + 1
                                                        )
                                                    sel = st.selectbox(
                                                        "",
                                                        ["(Không chọn)"] + headers,
                                                        index=di,
                                                        key=f"sp_req_{col}",
                                                        label_visibility="collapsed",
                                                    )
                                                    current_mapping[col] = (
                                                        None
                                                        if sel == "(Không chọn)"
                                                        else sel
                                                    )

                                            for col in conditional_cols:
                                                m = col_map.get(col)
                                                val = current_mapping.get(col)
                                                is_missing = val is None
                                                dot = (
                                                    "y"
                                                    if is_missing
                                                    else (
                                                        "g"
                                                        if m and m.confidence >= 90
                                                        else "y"
                                                    )
                                                )

                                                rc = st.columns([0.3, 1.5, 2.8])
                                                with rc[0]:
                                                    st.markdown(
                                                        f'<span class="sp-dot {dot}"></span>',
                                                        unsafe_allow_html=True,
                                                    )
                                                with rc[1]:
                                                    st.markdown(
                                                        f'<span style="font-size:13px;font-weight:500;">{col}<span class="sp-badge" style="background:#ca8a04;">THEO LOẠI</span></span>',
                                                        unsafe_allow_html=True,
                                                    )
                                                with rc[2]:
                                                    di = 0
                                                    cur = current_mapping.get(col)
                                                    if cur in headers:
                                                        di = headers.index(cur) + 1
                                                    elif (
                                                        m
                                                        and m.matched_header in headers
                                                    ):
                                                        di = (
                                                            headers.index(
                                                                m.matched_header
                                                            )
                                                            + 1
                                                        )
                                                    sel = st.selectbox(
                                                        "",
                                                        ["(Không chọn)"] + headers,
                                                        index=di,
                                                        key=f"sp_cond_{col}",
                                                        label_visibility="collapsed",
                                                    )
                                                    current_mapping[col] = (
                                                        None
                                                        if sel == "(Không chọn)"
                                                        else sel
                                                    )

                                            if opt_cols_list:
                                                with st.expander(
                                                    f"Không bắt buộc ({len(opt_cols_list)} trường)",
                                                    expanded=False,
                                                ):
                                                    for col in opt_cols_list:
                                                        m = col_map.get(col)
                                                        val = current_mapping.get(col)
                                                        dot = (
                                                            "g"
                                                            if m and m.confidence >= 90
                                                            else "y"
                                                            if m and m.confidence >= 50
                                                            else "r"
                                                        )

                                                        oc = st.columns([0.3, 1.8, 2.5])
                                                        with oc[0]:
                                                            st.markdown(
                                                                f'<span class="sp-dot {dot}"></span>',
                                                                unsafe_allow_html=True,
                                                            )
                                                        with oc[1]:
                                                            st.markdown(
                                                                f'<span style="font-size:13px;">{col}</span>',
                                                                unsafe_allow_html=True,
                                                            )
                                                        with oc[2]:
                                                            di = 0
                                                            cur = current_mapping.get(
                                                                col
                                                            )
                                                            if cur in headers:
                                                                di = (
                                                                    headers.index(cur)
                                                                    + 1
                                                                )
                                                            elif (
                                                                m
                                                                and m.matched_header
                                                                in headers
                                                            ):
                                                                di = (
                                                                    headers.index(
                                                                        m.matched_header
                                                                    )
                                                                    + 1
                                                                )
                                                            sel = st.selectbox(
                                                                "",
                                                                ["(Không chọn)"]
                                                                + headers,
                                                                index=di,
                                                                key=f"sp_opt_{col}",
                                                                label_visibility="collapsed",
                                                            )
                                                            current_mapping[col] = (
                                                                None
                                                                if sel == "(Không chọn)"
                                                                else sel
                                                            )

                                            missing_req = [
                                                c
                                                for c in required_cols
                                                if current_mapping.get(c) is None
                                            ]
                                            if missing_req:
                                                st.markdown(
                                                    f'<span style="color:#dc2626;font-size:13px;">Thiếu {len(missing_req)} cột bắt buộc</span>',
                                                    unsafe_allow_html=True,
                                                )

                                            if (
                                                match_result
                                                and match_result.unmatched_excel_headers
                                            ):
                                                u = match_result.unmatched_excel_headers[
                                                    0
                                                ]
                                                hint = ""
                                                if u.suggested_matches:
                                                    hint = f" Gợi ý: {u.suggested_matches[0].header} ({u.suggested_matches[0].confidence}%)"
                                                st.markdown(
                                                    f'<span style="color:#ca8a04;font-size:12px;">{len(match_result.unmatched_excel_headers)} cột chưa dùng{hint}</span>',
                                                    unsafe_allow_html=True,
                                                )

                                            st.markdown("---")
                                            tpl_name = st.text_input(
                                                "Lưu mẫu cấu hình hiện tại (nếu cần):",
                                                key="sp_confirm_tpl_name",
                                                placeholder="Nhập tên mẫu để lưu...",
                                            )
                                            c_back, c_save, c_next = st.columns(
                                                [1, 1, 1.5]
                                            )
                                            with c_back:
                                                if st.button(
                                                    "← Tải file khác",
                                                    use_container_width=True,
                                                    key="sp_confirm_back_1",
                                                ):
                                                    st.session_state.import_step = 1
                                                    st.rerun()
                                            with c_save:
                                                if st.button(
                                                    "💾 Lưu mẫu",
                                                    use_container_width=True,
                                                    key="sp_confirm_save_tpl",
                                                ):
                                                    if tpl_name.strip():
                                                        save_mapping_template(
                                                            tpl_name.strip(),
                                                            dict(current_mapping),
                                                        )
                                                        st.success("Đã lưu mẫu!")
                                                    else:
                                                        st.error(
                                                            "Vui lòng nhập tên mẫu."
                                                        )
                                            with c_next:
                                                if st.button(
                                                    "Kiểm tra dữ liệu →",
                                                    type="primary",
                                                    use_container_width=True,
                                                    key="sp_confirm_next_3",
                                                ):
                                                    missing_required = [
                                                        c
                                                        for c in required_cols
                                                        if current_mapping.get(c)
                                                        is None
                                                    ]
                                                    if missing_required:
                                                        st.error(
                                                            f"⚠️ Vui lòng ghép tất cả các cột bắt buộc: {', '.join(missing_required)}"
                                                        )
                                                    else:
                                                        st.session_state.import_step = 3
                                                        st.rerun()
                                        with col_right:
                                            st.caption("XEM TRƯỚC DỮ LIỆU GỐC")
                                            try:
                                                import io as _io
                                                import pandas as pd

                                                df_full = pd.read_excel(
                                                    _io.BytesIO(file_bytes),
                                                    sheet_name=selected_sheet,
                                                    header=header_row,
                                                )
                                                if not df_full.empty:
                                                    n = len(df_full)
                                                    st.markdown(
                                                        f'<span style="font-size:12px;color:#6b7280;">50 dòng đầu ({n} dòng — file gốc)</span>',
                                                        unsafe_allow_html=True,
                                                    )
                                                    st.dataframe(
                                                        df_full.head(50),
                                                        use_container_width=True,
                                                        height=200,
                                                    )
                                                    st.markdown(
                                                        '<span style="font-size:12px;color:#6b7280;">50 dòng cuối</span>',
                                                        unsafe_allow_html=True,
                                                    )
                                                    st.dataframe(
                                                        df_full.tail(50),
                                                        use_container_width=True,
                                                        height=200,
                                                    )
                                                else:
                                                    st.caption(
                                                        "Không có dữ liệu để xem trước"
                                                    )
                                            except Exception as _e:
                                                st.caption(
                                                    f"Không thể đọc dữ liệu xem trước: {_e}"
                                                )

                                    if st.session_state.import_step >= 3:
                                        st.caption("XEM TRƯỚC DỮ LIỆU ĐÃ GHÉP")

                                        nav_c1, nav_c2 = st.columns([1, 4])
                                        with nav_c1:
                                            if st.button(
                                                "← Quay lại sửa ghép cột",
                                                key="sp_confirm_back_2",
                                            ):
                                                st.session_state.import_step = 2
                                                st.rerun()
                                        st.markdown("---")

                                    if True:
                                        # Read & remap
                                        df_raw = parse_excel_to_df(
                                            file_bytes,
                                            header_row=header_row,
                                            sheet_name=selected_sheet,
                                        )
                                        df_parsed = remap_dataframe_columns(
                                            df_raw, current_mapping
                                        )

                                        if df_parsed.empty:
                                            st.info(
                                                "Không có dòng dữ liệu nào sau khi đọc."
                                            )
                                        elif len(df_parsed) > 100000:
                                            st.error(
                                                "File Excel qua lon (>100.000 dong). Vui long chia nho file."
                                            )
                                        else:
                                            # Validate
                                            if import_method == "activities":
                                                errors = validate_activities_data(
                                                    df_parsed, get_connection()
                                                )
                                            else:
                                                errors = validate_aggregate_totals_data(
                                                    df_parsed, get_connection()
                                                )

                                            if errors:
                                                st.error(
                                                    "❌ Phát hiện lỗi định dạng dữ liệu trong file Excel. Vui lòng sửa lại:"
                                                )
                                                for idx_e, r_num, err_msg in errors[
                                                    :20
                                                ]:
                                                    st.write(
                                                        f"- Dòng {r_num}: {err_msg}"
                                                    )
                                                if len(errors) > 20:
                                                    st.caption(
                                                        f"... và {len(errors) - 20} lỗi khác."
                                                    )
                                            else:
                                                st.success(
                                                    f"✓ Dữ liệu hợp lệ! Đã đọc thành công {len(df_parsed)} dòng."
                                                )

                                                # Diff
                                                if import_method == "activities":
                                                    df_diff = diff_activities(
                                                        df_parsed,
                                                        get_connection(),
                                                        selected_tf_name,
                                                    )
                                                else:
                                                    df_diff = diff_aggregate_totals(
                                                        df_parsed,
                                                        get_connection(),
                                                        selected_tf_name,
                                                    )

                                                # Diff counts
                                                counts = (
                                                    df_diff["diff_marker"]
                                                    .value_counts()
                                                    .to_dict()
                                                )
                                                c_new = counts.get("NEW", 0)
                                                c_upd = counts.get("UPDATE", 0)
                                                c_skip = counts.get("SKIP", 0)

                                                cols_m = st.columns(3)
                                                cols_m[0].metric("Thêm mới", c_new)
                                                cols_m[1].metric(
                                                    "Cập nhật / Thay đổi", c_upd
                                                )
                                                cols_m[2].metric(
                                                    "Trùng khớp (Bỏ qua)", c_skip
                                                )

                                                # Submit batch
                                                if st.button(
                                                    "🚀 Gửi yêu cầu phê duyệt",
                                                    type="primary",
                                                    key="btn_submit_batch_approve",
                                                ):
                                                    conn_write = get_connection()
                                                    try:
                                                        cur = conn_write.cursor()
                                                        cur.execute(
                                                            """
                                                            INSERT INTO import_batches (domain, dept_name, status, uploaded_by, filename, row_count)
                                                            VALUES (?, ?, 'pending', ?, ?, ?)
                                                        """,
                                                            (
                                                                import_method,
                                                                dept_name,
                                                                f"Code {dept_auth_code}",
                                                                uploaded_file.name,
                                                                len(df_diff),
                                                            ),
                                                        )
                                                        batch_id = cur.lastrowid

                                                        from pipeline.validator import (
                                                            parse_bool,
                                                            safe_float,
                                                        )

                                                        if (
                                                            import_method
                                                            == "activities"
                                                        ):
                                                            with st.spinner(
                                                                "Đang xử lý dữ liệu hoạt động..."
                                                            ):
                                                                import pandas as pd

                                                                for (
                                                                    idx_r,
                                                                    row,
                                                                ) in df_diff.iterrows():
                                                                    is_main = parse_bool(
                                                                        row.get(
                                                                            "Tác giả chính",
                                                                            False,
                                                                        )
                                                                    )
                                                                    is_foreign = parse_bool(
                                                                        row.get(
                                                                            "Giảng dạy tiếng nước ngoài",
                                                                            False,
                                                                        )
                                                                    )
                                                                    qty = safe_float(
                                                                        row["Số lượng"]
                                                                    )
                                                                    std_cnt = int(
                                                                        safe_float(
                                                                            row.get(
                                                                                "Số học viên",
                                                                                0,
                                                                            )
                                                                        )
                                                                        or 0
                                                                    )
                                                                    log_d_parsed = pd.to_datetime(
                                                                        row[
                                                                            "Ngày thực hiện"
                                                                        ]
                                                                    ).strftime(
                                                                        "%Y-%m-%d"
                                                                    )

                                                                    cur.execute(
                                                                        """
                                                                        INSERT INTO staging_activities (
                                                                            batch_id, row_num, diff_marker, diff_detail, validation_errors,
                                                                            teacher_name, activity_type_name, log_date, quantity,
                                                                            class_level, class_type, student_count, nckh_level,
                                                                            is_main_author, is_foreign_language_instruction, note, timeframe_name
                                                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                                                    """,
                                                                        (
                                                                            batch_id,
                                                                            idx_r
                                                                            + header_row
                                                                            + 2,
                                                                            row[
                                                                                "diff_marker"
                                                                            ],
                                                                            row[
                                                                                "diff_detail"
                                                                            ],
                                                                            "",
                                                                            row[
                                                                                "Mã GV"
                                                                            ],
                                                                            row[
                                                                                "Tên loại hoạt động"
                                                                            ],
                                                                            log_d_parsed,
                                                                            qty,
                                                                            row.get(
                                                                                "Cấp lớp",
                                                                                None,
                                                                            )
                                                                            if not pd.isna(
                                                                                row.get(
                                                                                    "Cấp lớp",
                                                                                    None,
                                                                                )
                                                                            )
                                                                            else None,
                                                                            row.get(
                                                                                "Loại lớp",
                                                                                None,
                                                                            )
                                                                            if not pd.isna(
                                                                                row.get(
                                                                                    "Loại lớp",
                                                                                    None,
                                                                                )
                                                                            )
                                                                            else None,
                                                                            std_cnt,
                                                                            row.get(
                                                                                "Cấp đề tài",
                                                                                None,
                                                                            )
                                                                            if not pd.isna(
                                                                                row.get(
                                                                                    "Cấp đề tài",
                                                                                    None,
                                                                                )
                                                                            )
                                                                            else None,
                                                                            is_main,
                                                                            is_foreign,
                                                                            row.get(
                                                                                "Ghi chú",
                                                                                None,
                                                                            )
                                                                            if not pd.isna(
                                                                                row.get(
                                                                                    "Ghi chú",
                                                                                    None,
                                                                                )
                                                                            )
                                                                            else None,
                                                                            selected_tf_name,
                                                                        ),
                                                                    )
                                                        else:  # aggregate_totals
                                                            with st.spinner(
                                                                "Đang xử lý dữ liệu tổng hợp..."
                                                            ):
                                                                for (
                                                                    idx_r,
                                                                    row,
                                                                ) in df_diff.iterrows():
                                                                    cur.execute(
                                                                        """
                                                                        INSERT INTO staging_aggregate_totals (
                                                                            batch_id, row_num, diff_marker, diff_detail, validation_errors,
                                                                            teacher_name, tong_gc_da_thuc_hien, nckh_da_thuc_hien,
                                                                            so_gio_duoc_mien_giam, dinh_muc_gc_phai_thuc_hien, note, timeframe_name
                                                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                                                    """,
                                                                        (
                                                                            batch_id,
                                                                            idx_r
                                                                            + header_row
                                                                            + 2,
                                                                            row[
                                                                                "diff_marker"
                                                                            ],
                                                                            row[
                                                                                "diff_detail"
                                                                            ],
                                                                            "",
                                                                            row[
                                                                                "Mã GV"
                                                                            ],
                                                                            safe_float(
                                                                                row[
                                                                                    "Tổng GC thực hiện"
                                                                                ]
                                                                            )
                                                                            or 0.0,
                                                                            safe_float(
                                                                                row[
                                                                                    "NCKH thực hiện"
                                                                                ]
                                                                            )
                                                                            or 0.0,
                                                                            safe_float(
                                                                                row[
                                                                                    "Số giờ miễn giảm"
                                                                                ]
                                                                            )
                                                                            or 0.0,
                                                                            safe_float(
                                                                                row[
                                                                                    "Định mức GC"
                                                                                ]
                                                                            )
                                                                            or 0.0,
                                                                            row.get(
                                                                                "Ghi chú",
                                                                                None,
                                                                            )
                                                                            if not pd.isna(
                                                                                row.get(
                                                                                    "Ghi chú",
                                                                                    None,
                                                                                )
                                                                            )
                                                                            else None,
                                                                            selected_tf_name,
                                                                        ),
                                                                    )

                                                        conn_write.commit()
                                                        st.success(
                                                            "🎉 Đã gửi yêu cầu phê duyệt đến Quản trị viên thành công!"
                                                        )
                                                        st.balloons()
                                                    except Exception as ex:
                                                        st.error(
                                                            f"Lỗi khi gửi yêu cầu: {ex}"
                                                        )
                                                    finally:
                                                        conn_write.close()
                            except Exception as e_headers:
                                st.error(
                                    "⚠️ **Lỗi đọc file Excel:** Không thể phân tích cấu trúc của file Excel được tải lên.\n\n"
                                    "**Gợi ý khắc phục:**\n"
                                    "- Đảm bảo file không bị lỗi, mật khẩu bảo vệ hoặc bị mã hóa.\n"
                                    "- Kiểm tra xem bạn đã chọn đúng tên Sheet và Dòng chứa tiêu đề cột (0-indexed) chưa.\n"
                                )
                                with st.expander("Chi tiết kỹ thuật"):
                                    st.code(str(e_headers))

conn.close()
