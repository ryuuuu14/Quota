import streamlit as st
import json
from datetime import datetime
from database import get_connection, init_db
from components import (
    render_sidebar,
    render_empty_state,
    render_diff_viewer,
)
from pipeline.differ import VALID_DOMAINS


# ── Helper: parse a raw date-range string into (start_date, end_date) ──────────
def _parse_date_range(raw: str):
    """Return (start_date, end_date) as date objects, or (None, None) on failure."""
    import re

    raw = str(raw).strip()
    if not raw or raw.lower() in ("none", "nan", ""):
        return None, None

    # Normalise separators: ' - ', ' to ', ' đến ' (spaces required to avoid splitting ISO dates)
    sep_pattern = r"\s+(?:đến|to)\s+|\s+-\s+"
    parts = re.split(sep_pattern, raw, maxsplit=1)

    def _try_parse(s):
        s = s.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                pass
        # Try pandas as last resort
        try:
            import pandas as pd

            return pd.to_datetime(s, dayfirst=True).date()
        except Exception:
            return None

    if len(parts) == 2:
        d1 = _try_parse(parts[0])
        d2 = _try_parse(parts[1])
        if d1 and d2:
            return (d1, d2) if d1 <= d2 else (d2, d1)
    elif len(parts) == 1:
        d = _try_parse(parts[0])
        if d:
            return d, d  # single-day leave
    return None, None


def _months_between(d1, d2) -> float:
    """Return fractional months between two date objects."""
    if d1 is None or d2 is None:
        return 0.0
    from dateutil.relativedelta import relativedelta

    rd = relativedelta(d2, d1)
    return rd.years * 12 + rd.months + rd.days / 30.0


def _insert_leave_reductions(cursor, teacher_id: int, staging_row, now_str: str):
    """
    Parse study_leave / field_trip / permitted_leave from staging_row.
    Determine the correct reduction_rule_id and insert REDUCTION history records.
    """
    leave_fields = [
        ("study_leave", "study"),
        ("field_trip", "field_trip"),
        ("permitted_leave", "permitted"),
    ]

    for col, leave_type in leave_fields:
        raw = staging_row.get(col)
        import pandas as pd

        if pd.isna(raw) if hasattr(pd, "isna") else (raw is None):
            continue
        raw = str(raw).strip()
        if not raw or raw.lower() in ("none", "nan", ""):
            continue

        start_d, end_d = _parse_date_range(raw)
        if start_d is None:
            continue

        duration_months = _months_between(start_d, end_d)

        # Determine rule name based on leave type and duration
        if leave_type == "study":
            if duration_months >= 10:
                rule_name = "Đi học / Bồi dưỡng (từ 10 tháng trở lên)"
            elif duration_months >= 6:
                rule_name = "Đi học / Bồi dưỡng (từ 6 đến dưới 10 tháng)"
            else:
                rule_name = "Đi học / Bồi dưỡng (dưới 6 tháng)"
        elif leave_type == "field_trip":
            if duration_months >= 10:
                rule_name = "Đi thực tế / Trưng tập (từ 10 tháng trở lên)"
            else:
                rule_name = "Đi thực tế / Trưng tập (dưới 10 tháng)"
        else:  # permitted_leave
            rule_name = "Nghỉ có phép"

        # Look up reduction rule id
        cursor.execute(
            "SELECT id FROM reduction_rules WHERE name = ? LIMIT 1", (rule_name,)
        )
        rule_row = cursor.fetchone()
        if not rule_row:
            continue  # Rule not seeded — skip silently

        rule_id = rule_row["id"]
        start_str = start_d.isoformat()
        end_str = end_d.isoformat() if end_d else start_str

        # Avoid duplicate REDUCTION records for the same rule + period
        cursor.execute(
            """
            SELECT id FROM teacher_role_history
            WHERE teacher_id = ? AND record_type = 'REDUCTION'
              AND value_text = ? AND start_date = ?
        """,
            (teacher_id, str(rule_id), start_str),
        )
        if cursor.fetchone():
            continue  # Already inserted

        cursor.execute(
            """
            INSERT INTO teacher_role_history
                (teacher_id, record_type, value_text, start_date, end_date)
            VALUES (?, 'REDUCTION', ?, ?, ?)
        """,
            (teacher_id, str(rule_id), start_str, end_str),
        )


# ── Dialog: show batch detail ─────────────────────────────────────────────
@st.dialog("🔎 Chi tiết Lô dữ liệu", width="large")
def show_batch_detail(batch_id: int):
    import pandas as pd
    from database import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM import_batches WHERE id = ?", (batch_id,))
    batch = cursor.fetchone()
    if not batch or batch["status"] != "pending":
        st.info("Lô dữ liệu này không còn ở trạng thái chờ duyệt.")
        if st.button("Đóng"):
            st.rerun()
        conn.close()
        return

    domain = batch["domain"]
    dept_name = batch["dept_name"]

    if domain == "reduction_rules":
        diff_data = json.loads(batch["diff_json"]) if batch["diff_json"] else {}
        action = diff_data.get("action", "")
        rule_id = diff_data.get("id")
        name = diff_data.get("name", "")
        rule_type = diff_data.get("rule_type", "")
        teaching_pct = diff_data.get("teaching_reduction_pct", 0.0)
        nckh_pct = diff_data.get("nckh_reduction_pct", 0.0)

        action_label = {
            "create": "Thêm mới",
            "update": "Cập nhật/Sửa",
            "delete": "Xóa",
        }.get(action, action)
        type_label = {"ROLE": "Chức vụ Quản lý", "SPECIAL": "Diện miễn giảm khác"}.get(
            rule_type, rule_type
        )

        st.markdown(f"#### Chi tiết yêu cầu: **{action_label}**")
        st.markdown(f"""
        - **Tên quy tắc**: `{name}`
        - **Phân loại**: {type_label}
        - **Tỷ lệ miễn Giảng dạy**: `{teaching_pct}%`
        - **Tỷ lệ miễn NCKH**: `{nckh_pct}%`
        """)

        st.markdown("### ✍️ Quyết định phê duyệt")
        rejection_reason = st.text_input(
            "Lý do từ chối (bắt buộc nếu từ chối):", key="rejection_reason_input"
        )

        col_act1, col_act2 = st.columns(2)

        if col_act1.button(
            "✅ Phê duyệt & Đưa vào hệ thống", type="primary", key="btn_approve_batch"
        ):
            try:
                with conn:
                    cursor = conn.cursor()
                    decided_by = st.session_state["admin_username"]
                    now_str = datetime.now().isoformat()

                    if action == "create":
                        cursor.execute(
                            """
                            INSERT INTO reduction_rules (name, rule_type, teaching_reduction_pct, nckh_reduction_pct)
                            VALUES (?, ?, ?, ?)
                        """,
                            (name, rule_type, teaching_pct, nckh_pct),
                        )
                    elif action == "update":
                        cursor.execute(
                            """
                            UPDATE reduction_rules
                            SET name = ?, teaching_reduction_pct = ?, nckh_reduction_pct = ?
                            WHERE id = ?
                        """,
                            (name, teaching_pct, nckh_pct, rule_id),
                        )
                    elif action == "delete":
                        cursor.execute(
                            "DELETE FROM reduction_rules WHERE id = ?", (rule_id,)
                        )

                    cursor.execute(
                        """
                        UPDATE import_batches
                        SET status = 'approved', decided_at = ?, decided_by = ?
                        WHERE id = ?
                    """,
                        (now_str, decided_by, batch_id),
                    )

                    cursor.execute(
                        """
                        INSERT INTO notifications (target_dept, target_role, title, message, batch_id)
                        VALUES (?, 'head', '✅ Yêu cầu phê duyệt thành công', ?, ?)
                    """,
                        (
                            dept_name,
                            f"Lô dữ liệu #{batch_id} đã được phê duyệt.",
                            batch_id,
                        ),
                    )

                st.success("✅ Đã phê duyệt và cập nhật dữ liệu thành công!")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi khi phê duyệt: {str(e)}")

        if col_act2.button("❌ Từ chối yêu cầu", key="btn_reject_batch"):
            if not rejection_reason.strip():
                st.error("Vui lòng nhập lý do từ chối.")
            else:
                try:
                    with conn:
                        cursor = conn.cursor()
                        decided_by = st.session_state["admin_username"]
                        now_str = datetime.now().isoformat()

                        cursor.execute(
                            """
                            UPDATE import_batches
                            SET status = 'rejected', rejection_reason = ?, decided_at = ?, decided_by = ?
                            WHERE id = ?
                        """,
                            (rejection_reason, now_str, decided_by, batch_id),
                        )

                        cursor.execute(
                            """
                            INSERT INTO notifications (target_dept, target_role, title, message, batch_id)
                            VALUES (?, 'head', '❌ Yêu cầu bị từ chối', ?, ?)
                        """,
                            (
                                dept_name,
                                f"Lô dữ liệu #{batch_id} bị từ chối. Lý do: {rejection_reason}",
                                batch_id,
                            ),
                        )

                    st.success("❌ Đã từ chối lô dữ liệu và phản hồi lại Đơn vị.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi từ chối: {str(e)}")
    else:
        if domain not in VALID_DOMAINS:
            st.error(f"Lĩnh vực không hợp lệ: '{domain}'")
            conn.close()
            return

        staging_table = f"staging_{domain}"
        staging_df = pd.read_sql_query(
            f"""
            SELECT * FROM {staging_table}
            WHERE batch_id = ?
            ORDER BY row_num ASC
        """,
            conn,
            params=(batch_id,),
        )

        if staging_df.empty:
            st.info("Lô dữ liệu trống hoặc không có dòng hợp lệ.")
        else:
            diff_json_str = batch["diff_json"] or "{}"

            view_mode_key = f"view_mode_{batch_id}"
            if view_mode_key not in st.session_state:
                st.session_state[view_mode_key] = "inline"

            col_view, _ = st.columns([1, 3])
            with col_view:
                st.session_state[view_mode_key] = (
                    "side_by_side"
                    if st.toggle(
                        "Xem dạng cạnh nhau",
                        value=(st.session_state[view_mode_key] == "side_by_side"),
                        key=f"view_toggle_{batch_id}",
                    )
                    else "inline"
                )

            render_diff_viewer(
                staging_df=staging_df,
                diff_json_str=diff_json_str,
                domain=domain,
                batch_id=batch_id,
                view_mode=st.session_state[view_mode_key],
                key_prefix="pheduyet",
            )

            st.markdown("### ✍️ Quyết định phê duyệt")

            admin_remarks = st.text_area(
                "📝 Nhận xét / Hướng dẫn của Quản trị viên (gửi lại Đơn vị):",
                value=batch["remarks"] if "remarks" in batch.keys() else "",
                key=f"admin_remarks_{batch_id}",
                placeholder="Nhập nhận xét bằng Markdown...",
            )

            rejection_reason = st.text_input(
                "Lý do từ chối (bắt buộc nếu từ chối):",
                key=f"rejection_reason_input_{batch_id}",
            )

            col_act1, col_act2 = st.columns(2)

            def _save_remarks(c, b_id, remarks_text):
                c.execute(
                    "UPDATE import_batches SET remarks = ? WHERE id = ?",
                    (remarks_text, b_id),
                )

            if col_act1.button(
                "✅ Phê duyệt & Đưa vào hệ thống",
                type="primary",
                key="btn_approve_batch",
            ):
                try:
                    with conn:
                        cursor = conn.cursor()
                        decided_by = st.session_state["admin_username"]
                        now_str = datetime.now().isoformat()

                        _save_remarks(cursor, batch_id, admin_remarks)

                    if domain == "teachers":
                        for _, r in staging_df.iterrows():
                            marker = r["diff_marker"]
                            if marker == "NEW":
                                cursor.execute(
                                    """
                                    INSERT INTO teachers (name, subject_group, is_female, employment_type, guest_rank, total_12m_salary, police_rank_id, salary_coefficient)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                    (
                                        r["teacher_name"],
                                        r["subject_group"],
                                        r["is_female"],
                                        r["employment_type"],
                                        r["guest_rank"],
                                        r["total_12m_salary"],
                                        r["police_rank_id"],
                                        r["salary_coefficient"],
                                    ),
                                )
                                new_id = cursor.lastrowid

                                title_s_dt = (
                                    r["title_start_date"]
                                    if pd.notna(r.get("title_start_date"))
                                    and str(r.get("title_start_date")).strip()
                                    else now_str[:10]
                                )
                                role_s_dt = (
                                    r["role_start_date"]
                                    if pd.notna(r.get("role_start_date"))
                                    and str(r.get("role_start_date")).strip()
                                    else now_str[:10]
                                )

                                cursor.execute(
                                    """
                                    INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
                                    VALUES (?, 'TITLE', ?, ?)
                                """,
                                    (new_id, r["title"], title_s_dt),
                                )
                                cursor.execute(
                                    """
                                    INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
                                    VALUES (?, 'DEPARTMENT', ?, ?)
                                """,
                                    (new_id, r["department"], role_s_dt),
                                )
                                if r.get("role"):
                                    cursor.execute(
                                        """
                                        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
                                        VALUES (?, 'ROLE', ?, ?)
                                    """,
                                        (new_id, r["role"], role_s_dt),
                                    )
                                _insert_leave_reductions(cursor, new_id, r, now_str)

                            elif marker == "UPDATE":
                                t_id = r.get("teacher_id")
                                if pd.isna(t_id):
                                    t_id = None

                                if t_id:
                                    cursor.execute(
                                        """
                                        SELECT t.id,
                                               (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'TITLE' ORDER BY start_date DESC LIMIT 1) as title,
                                               (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'DEPARTMENT' ORDER BY start_date DESC LIMIT 1) as dept,
                                               (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'ROLE' ORDER BY start_date DESC LIMIT 1) as role
                                        FROM teachers t WHERE t.id = ?
                                    """,
                                        (t_id,),
                                    )
                                else:
                                    cursor.execute(
                                        """
                                        SELECT t.id,
                                               (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'TITLE' ORDER BY start_date DESC LIMIT 1) as title,
                                               (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'DEPARTMENT' ORDER BY start_date DESC LIMIT 1) as dept,
                                               (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'ROLE' ORDER BY start_date DESC LIMIT 1) as role
                                        FROM teachers t WHERE t.name = ?
                                    """,
                                        (r["teacher_name"],),
                                    )
                                gvs = cursor.fetchall()
                                old_title = None
                                old_dept = None
                                old_role = None

                                if not t_id:
                                    for gv in gvs:
                                        if (
                                            str(gv["dept"]).strip().lower()
                                            == str(r["department"]).strip().lower()
                                        ):
                                            t_id = gv["id"]
                                            old_title = gv["title"]
                                            old_dept = gv["dept"]
                                            old_role = gv["role"]
                                            break
                                elif gvs:
                                    old_title = gvs[0]["title"]
                                    old_dept = gvs[0]["dept"]
                                    old_role = gvs[0]["role"]

                                if t_id:
                                    cursor.execute(
                                        """
                                        UPDATE teachers
                                        SET subject_group = ?, is_female = ?, employment_type = ?, guest_rank = ?
                                        WHERE id = ?
                                    """,
                                        (
                                            r["subject_group"],
                                            r["is_female"],
                                            r["employment_type"],
                                            r["guest_rank"],
                                            t_id,
                                        ),
                                    )

                                    title_s_dt = (
                                        r["title_start_date"]
                                        if pd.notna(r.get("title_start_date"))
                                        and str(r.get("title_start_date")).strip()
                                        else now_str[:10]
                                    )
                                    role_s_dt = (
                                        r["role_start_date"]
                                        if pd.notna(r.get("role_start_date"))
                                        and str(r.get("role_start_date")).strip()
                                        else now_str[:10]
                                    )

                                    if r["title"] and r["title"] != old_title:
                                        cursor.execute(
                                            "UPDATE teacher_role_history SET end_date = date(?, '-1 day') WHERE teacher_id = ? AND record_type = 'TITLE' AND end_date IS NULL",
                                            (title_s_dt, t_id),
                                        )
                                        cursor.execute(
                                            "INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (?, 'TITLE', ?, ?)",
                                            (t_id, r["title"], title_s_dt),
                                        )

                                    if r["department"] and r["department"] != old_dept:
                                        cursor.execute(
                                            "UPDATE teacher_role_history SET end_date = date(?, '-1 day') WHERE teacher_id = ? AND record_type = 'DEPARTMENT' AND end_date IS NULL",
                                            (role_s_dt, t_id),
                                        )
                                        cursor.execute(
                                            "INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (?, 'DEPARTMENT', ?, ?)",
                                            (t_id, r["department"], role_s_dt),
                                        )

                                    if r.get("role") and r["role"] != old_role:
                                        cursor.execute(
                                            "UPDATE teacher_role_history SET end_date = date(?, '-1 day') WHERE teacher_id = ? AND record_type = 'ROLE' AND end_date IS NULL",
                                            (role_s_dt, t_id),
                                        )
                                        cursor.execute(
                                            "INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (?, 'ROLE', ?, ?)",
                                            (t_id, r["role"], role_s_dt),
                                        )

                                    _insert_leave_reductions(cursor, t_id, r, now_str)

                            elif marker == "DELETE":
                                t_id = r.get("teacher_id")
                                if pd.isna(t_id):
                                    t_id = None
                                if t_id:
                                    cursor.execute(
                                        "DELETE FROM session_teacher_totals WHERE teacher_id = ?",
                                        (t_id,),
                                    )
                                    cursor.execute(
                                        "DELETE FROM activity_logs WHERE teacher_id = ?",
                                        (t_id,),
                                    )
                                    cursor.execute(
                                        "DELETE FROM teacher_role_history WHERE teacher_id = ?",
                                        (t_id,),
                                    )
                                    cursor.execute(
                                        "DELETE FROM teacher_rank_history WHERE teacher_id = ?",
                                        (t_id,),
                                    )
                                    cursor.execute(
                                        "DELETE FROM manual_conversions WHERE teacher_id = ?",
                                        (t_id,),
                                    )
                                    cursor.execute(
                                        "DELETE FROM payroll_records WHERE teacher_id = ?",
                                        (t_id,),
                                    )
                                    cursor.execute(
                                        "DELETE FROM teachers WHERE id = ?", (t_id,)
                                    )

                    elif domain == "activities":
                        cursor.execute("SELECT id, name FROM timeframes")
                        tf_map = {
                            row["name"].strip().lower(): row["id"]
                            for row in cursor.fetchall()
                        }
                        cursor.execute("SELECT id, name FROM teachers")
                        t_map = {
                            row["name"].strip().lower(): row["id"]
                            for row in cursor.fetchall()
                        }

                        cursor.execute("SELECT * FROM activity_types")
                        act_types_list = cursor.fetchall()
                        act_map = {
                            row["name"].strip().lower(): row["id"]
                            for row in act_types_list
                        }

                        for _, r in staging_df.iterrows():
                            if r["diff_marker"] == "NEW":
                                try:
                                    t_id = int(float(str(r["teacher_name"]).strip()))
                                except Exception:
                                    t_id = None
                                tf_id = tf_map.get(
                                    str(r["timeframe_name"]).strip().lower()
                                )
                                act_name_lower = (
                                    str(r["activity_type_name"]).strip().lower()
                                )

                                if act_name_lower not in act_map:
                                    cursor.execute(
                                        "INSERT INTO activity_types (name, category, unit, base_conversion_rate) VALUES (?, 'Khác', 'Giờ', 1.0)",
                                        (r["activity_type_name"],),
                                    )
                                    act_id = cursor.lastrowid
                                    act_map[act_name_lower] = act_id
                                else:
                                    act_id = act_map[act_name_lower]

                                if t_id and tf_id:
                                    cursor.execute(
                                        "SELECT * FROM activity_types WHERE id = ?",
                                        (act_id,),
                                    )
                                    act_row = cursor.fetchone()

                                    log_row_dict = {
                                        "quantity": r["quantity"],
                                        "class_level": r["class_level"],
                                        "class_type": r["class_type"],
                                        "student_count": r["student_count"],
                                        "nckh_level": r["nckh_level"],
                                        "is_main_author": r["is_main_author"],
                                        "is_foreign_language_instruction": r[
                                            "is_foreign_language_instruction"
                                        ],
                                    }
                                    from calculations import calculate_activity_hours

                                    conv_hours = calculate_activity_hours(
                                        log_row_dict, dict(act_row)
                                    )

                                    cursor.execute(
                                        """
                                        INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity, class_level, class_type, student_count, nckh_level, is_main_author, is_foreign_language_instruction, note, timeframe_id, converted_hours)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                        (
                                            t_id,
                                            act_id,
                                            r["log_date"],
                                            r["quantity"],
                                            r["class_level"],
                                            r["class_type"],
                                            r["student_count"],
                                            r["nckh_level"],
                                            r["is_main_author"],
                                            r["is_foreign_language_instruction"],
                                            r["note"],
                                            tf_id,
                                            conv_hours,
                                        ),
                                    )

                    elif domain == "schedule":
                        cursor.execute("SELECT id, name FROM timeframes")
                        tf_map = {
                            row["name"].strip().lower(): row["id"]
                            for row in cursor.fetchall()
                        }
                        cursor.execute("SELECT id, name FROM teachers")
                        t_map = {
                            row["name"].strip().lower(): row["id"]
                            for row in cursor.fetchall()
                        }

                        for _, r in staging_df.iterrows():
                            marker = r["diff_marker"]
                            tf_id = tf_map.get(str(r["timeframe_name"]).strip().lower())
                            t_id = t_map.get(str(r["teacher_name"]).strip().lower())

                            if not t_id:
                                continue

                            if marker == "NEW":
                                cursor.execute(
                                    """
                                    INSERT INTO bulk_teaching_assignments (timeframe_id, teacher_id, subject_name, loai, nhom, si_so, tiet_quy_doi, he_so_tin_chi, ghi_chu, he_so_lop_dong, tiet_thuc_day)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                    (
                                        tf_id,
                                        t_id,
                                        r["subject_name"],
                                        r["loai"],
                                        r["nhom"],
                                        r["si_so"],
                                        r["tiet_quy_doi"],
                                        r["he_so_tin_chi"],
                                        r["validation_errors"],
                                        r["he_so_lop_dong"] or 1.0,
                                        r["tiet_thuc_day"] or 0.0,
                                    ),
                                )
                            elif marker == "UPDATE":
                                cursor.execute(
                                    """
                                    UPDATE bulk_teaching_assignments
                                    SET si_so = ?, tiet_quy_doi = ?, he_so_tin_chi = ?, he_so_lop_dong = ?, tiet_thuc_day = ?
                                    WHERE timeframe_id = ? AND teacher_id = ? AND subject_name = ? AND loai = ? AND nhom = ?
                                """,
                                    (
                                        r["si_so"],
                                        r["tiet_quy_doi"],
                                        r["he_so_tin_chi"],
                                        r["he_so_lop_dong"] or 1.0,
                                        r["tiet_thuc_day"] or 0.0,
                                        tf_id,
                                        t_id,
                                        r["subject_name"],
                                        r["loai"],
                                        r["nhom"],
                                    ),
                                )

                    elif domain == "aggregate_totals":
                        cursor.execute("SELECT id, name FROM timeframes")
                        tf_map = {
                            row["name"].strip().lower(): row["id"]
                            for row in cursor.fetchall()
                        }
                        cursor.execute("SELECT id, name FROM teachers")
                        t_rows = cursor.fetchall()
                        t_map_id = {str(row["id"]): row["id"] for row in t_rows}
                        t_map_name = {
                            row["name"].strip().lower(): row["id"] for row in t_rows
                        }

                        for _, r in staging_df.iterrows():
                            tf_id = tf_map.get(str(r["timeframe_name"]).strip().lower())
                            teacher_raw = str(r["teacher_name"]).strip()
                            t_id = t_map_id.get(teacher_raw)
                            if not t_id:
                                t_id = t_map_name.get(teacher_raw.lower())
                            if not t_id or not tf_id:
                                continue

                            cursor.execute(
                                """
                                INSERT INTO teacher_calculated_totals (
                                    timeframe_id, teacher_id, tong_gc_da_thuc_hien, nckh_da_thuc_hien, so_gio_duoc_mien_giam, dinh_muc_gc_phai_thuc_hien, is_override
                                ) VALUES (?, ?, ?, ?, ?, ?, 1)
                                ON CONFLICT(timeframe_id, teacher_id) DO UPDATE SET
                                    tong_gc_da_thuc_hien=excluded.tong_gc_da_thuc_hien,
                                    nckh_da_thuc_hien=excluded.nckh_da_thuc_hien,
                                    so_gio_duoc_mien_giam=excluded.so_gio_duoc_mien_giam,
                                    dinh_muc_gc_phai_thuc_hien=excluded.dinh_muc_gc_phai_thuc_hien,
                                    is_override=1
                            """,
                                (
                                    tf_id,
                                    t_id,
                                    r["tong_gc_da_thuc_hien"],
                                    r["nckh_da_thuc_hien"],
                                    r["so_gio_duoc_mien_giam"],
                                    r["dinh_muc_gc_phai_thuc_hien"],
                                ),
                            )

                    cursor.execute(
                        """
                        UPDATE import_batches
                        SET status = 'approved', decided_at = ?, decided_by = ?
                        WHERE id = ?
                    """,
                        (now_str, decided_by, batch_id),
                    )

                    cursor.execute(
                        """
                        INSERT INTO notifications (target_dept, target_role, title, message, batch_id)
                        VALUES (?, 'head', '✅ Yêu cầu phê duyệt thành công', ?, ?)
                    """,
                        (
                            dept_name,
                            f"Lô dữ liệu #{batch_id} đã được phê duyệt.",
                            batch_id,
                        ),
                    )

                    cursor.execute(
                        f"DELETE FROM {staging_table} WHERE batch_id = ?", (batch_id,)
                    )

                    st.success("✅ Đã phê duyệt và cập nhật dữ liệu thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi phê duyệt: {str(e)}")

            if col_act2.button(
                "❌ Từ chối yêu cầu", key="btn_reject_batch", type="secondary"
            ):
                if not rejection_reason.strip():
                    st.error("Vui lòng nhập lý do từ chối.")
                else:
                    try:
                        with conn:
                            cursor = conn.cursor()
                            decided_by = st.session_state["admin_username"]
                            now_str = datetime.now().isoformat()

                            _save_remarks(cursor, batch_id, admin_remarks)
                            conn.commit()

                            cursor.execute(
                                """
                                UPDATE import_batches
                                SET status = 'rejected', rejection_reason = ?, decided_at = ?, decided_by = ?
                                WHERE id = ?
                            """,
                                (rejection_reason, now_str, decided_by, batch_id),
                            )

                            cursor.execute(
                                """
                                INSERT INTO notifications (target_dept, target_role, title, message, batch_id)
                                VALUES (?, 'head', '❌ Yêu cầu bị từ chối', ?, ?)
                            """,
                                (
                                    dept_name,
                                    f"Lô dữ liệu #{batch_id} bị từ chối. Lý do: {rejection_reason}",
                                    batch_id,
                                ),
                            )

                            cursor.execute(
                                f"DELETE FROM {staging_table} WHERE batch_id = ?",
                                (batch_id,),
                            )

                        st.success("❌ Đã từ chối lô dữ liệu và phản hồi lại Đơn vị.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi từ chối: {str(e)}")

    conn.close()


if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

st.set_page_config(page_title="Phê duyệt Dữ liệu", page_icon="⚖️", layout="wide")
render_sidebar("pheduyet")

# Ensure user is logged in as Admin
# Test compatibility: st.session_state.get("is_admin", False)
from auth import require_role

if not require_role(["admin"], page_title="⚖️ Phê duyệt Yêu cầu Nhập dữ liệu"):
    st.stop()

# If authenticated admin
col1, col2, col3 = st.columns([1, 10, 1])
with col2:
    st.markdown('<div style="margin-bottom: 24px;">', unsafe_allow_html=True)
    st.title("⚖️ Bảng Phê duyệt Yêu cầu Nhập dữ liệu")
    st.markdown(
        """
    <div style="font-size: 1.05rem; color: var(--md-on-surface-variant); margin-top: -8px; margin-bottom: 24px; line-height: 1.6;">
        Xem xét, đối chiếu và phê duyệt các lô dữ liệu tải lên từ các Đơn vị giảng dạy.
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    conn = get_connection()
    import pandas as pd

    batches_df = pd.read_sql_query(
        """
        SELECT * FROM import_batches 
        ORDER BY 
            CASE status 
                WHEN 'pending' THEN 0 
                WHEN 'approved' THEN 1 
                ELSE 2 
            END,
            created_at DESC
    """,
        conn,
    )

    status_filter = st.selectbox(
        "Lọc theo trạng thái:", ["Tất cả", "Pending", "Approved", "Rejected"], index=1
    )
    if status_filter != "Tất cả":
        batches_df = batches_df[batches_df["status"] == status_filter.lower()]

    if batches_df.empty:
        render_empty_state("Hiện không có yêu cầu phê duyệt nào đang chờ.")
        conn.close()
        st.stop()

    st.markdown(f"### 📋 Danh sách Yêu cầu ({len(batches_df)})")

    # Let's list pending batches
    for idx, row in batches_df.iterrows():
        batch_id = int(row["id"])
        domain = row["domain"]
        status = row["status"]
        dept_name = row["dept_name"] or "Quản trị viên"
        uploaded_by = row["uploaded_by"]
        filename = row["filename"]
        row_count = row["row_count"]
        created_at = row["created_at"]

        status_variant = (
            "amber"
            if status == "pending"
            else "green"
            if status == "approved"
            else "red"
        )
        status_label = (
            "Chờ duyệt"
            if status == "pending"
            else "Đã duyệt"
            if status == "approved"
            else "Từ chối"
        )

        domain_label = {
            "teachers": "Hồ sơ Cán bộ",
            "activities": "Hoạt động miễn giảm/NCKH",
            "schedule": "Thời khóa biểu giảng dạy",
            "reduction_rules": "Yêu cầu quy tắc miễn giảm",
        }.get(domain, domain)

        with st.container():
            st.markdown(
                f"""
            <div class="md-card" style="padding: 16px 20px !important; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <span class="md-chip md-chip-primary" style="margin-right: 8px;">{domain_label}</span>
                        <span class="md-chip md-chip-{status_variant}">{status_label}</span>
                        <strong>Lô #{batch_id}</strong> &nbsp;|&nbsp; Đơn vị: <strong>{dept_name}</strong>
                        <div style="font-size: 0.85rem; color: var(--md-on-surface-variant); margin-top: 4px;">
                            Người tải lên: {uploaded_by} &nbsp;•&nbsp; File: <code>{filename}</code> ({row_count} dòng) &nbsp;•&nbsp; Thời gian: {created_at}
                        </div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button(f"🔍 Xem chi tiết Lô #{batch_id}", key=f"btn_view_{batch_id}"):
                show_batch_detail(batch_id)

    conn.close()
