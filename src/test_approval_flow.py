import os
from datetime import datetime
from database import init_db, seed_initial_data, get_connection


def test_approval_workflow_teachers(tmp_path):
    test_db = os.path.join(tmp_path, "test_approval.sqlite")
    os.environ["DB_PATH"] = test_db

    init_db()
    seed_initial_data()

    import seed_teachers

    seed_teachers.run()

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Create a pending import batch
    cursor.execute("""
        INSERT INTO import_batches (domain, dept_name, uploaded_by, filename, row_count, status)
        VALUES ('teachers', 'Khoa CNTT', 'test_user', 'gv.xlsx', 2, 'pending')
    """)
    batch_id = cursor.lastrowid

    # 2. Add staging records
    # A new teacher
    cursor.execute(
        """
        INSERT INTO staging_teachers (
            batch_id, row_num, teacher_name, department, title, employment_type,
            guest_rank, total_12m_salary, police_rank_id, salary_coefficient, is_female, subject_group, diff_marker, diff_detail, teacher_id
        ) VALUES (?, 1, 'Nguyễn Văn New', 'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học', 'Giảng viên', 'TEACHER', NULL, 20000000.0, NULL, 4.4, 0, 'Tự nhiên/Kỹ thuật', 'NEW', 'Cán bộ mới', 9999)
    """,
        (batch_id,),
    )

    # An updated teacher (Nguyễn Văn A is seeded by default)
    # Let's verify Nguyễn Văn A exists
    cursor.execute("SELECT id FROM teachers WHERE name = 'Nguyễn Văn A'")
    t_a = cursor.fetchone()
    assert t_a is not None

    cursor.execute(
        """
        INSERT INTO staging_teachers (
            batch_id, row_num, teacher_name, department, title, employment_type,
            guest_rank, total_12m_salary, police_rank_id, salary_coefficient, is_female, subject_group, diff_marker, diff_detail
        ) VALUES (?, 2, 'Nguyễn Văn A', 'Chính trị, Pháp luật, Nghiệp vụ', 'Giáo sư', 'TEACHER', NULL, 24000000.0, NULL, 6.2, 0, 'Chính trị/Nghiệp vụ', 'UPDATE', 'Chức danh: Giảng viên -> Giáo sư')
    """,
        (batch_id,),
    )

    conn.commit()

    # 3. Simulate approval process
    cursor.execute("SELECT * FROM staging_teachers WHERE batch_id = ?", (batch_id,))
    staging_rows = cursor.fetchall()
    assert len(staging_rows) == 2

    # Run the approval code
    decided_by = "admin"
    now_str = datetime.now().isoformat()

    for r in staging_rows:
        marker = r["diff_marker"]
        if marker == "NEW":
            t_id_val = int(r["teacher_id"]) if "teacher_id" in r.keys() and r["teacher_id"] is not None else None
            if t_id_val is not None:
                cursor.execute(
                    """
                    INSERT INTO teachers (id, name, subject_group, is_female, employment_type, guest_rank, total_12m_salary, police_rank_id, salary_coefficient)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        t_id_val,
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
                new_id = t_id_val
            else:
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

            cursor.execute(
                """
                INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
                VALUES (?, 'TITLE', ?, ?)
            """,
                (new_id, r["title"], now_str[:10]),
            )
            cursor.execute(
                """
                INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
                VALUES (?, 'DEPARTMENT', ?, ?)
            """,
                (new_id, r["department"], now_str[:10]),
            )

        elif marker == "UPDATE":
            cursor.execute(
                """
                SELECT t.id, 
                       (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'TITLE' ORDER BY start_date DESC LIMIT 1) as title,
                       (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'DEPARTMENT' ORDER BY start_date DESC LIMIT 1) as dept
                FROM teachers t WHERE t.name = ?
            """,
                (r["teacher_name"],),
            )
            gvs = cursor.fetchall()
            t_id = None
            old_title = None
            old_dept = None
            for gv in gvs:
                if (
                    str(gv["dept"]).strip().lower()
                    == str(r["department"]).strip().lower()
                ):
                    t_id = gv["id"]
                    old_title = gv["title"]
                    old_dept = gv["dept"]
                    break

            if t_id:
                cursor.execute(
                    """
                    UPDATE teachers 
                    SET subject_group = ?, is_female = ?, employment_type = ?, guest_rank = ?, total_12m_salary = ?, police_rank_id = ?, salary_coefficient = ?
                    WHERE id = ?
                """,
                    (
                        r["subject_group"],
                        r["is_female"],
                        r["employment_type"],
                        r["guest_rank"],
                        r["total_12m_salary"],
                        r["police_rank_id"],
                        r["salary_coefficient"],
                        t_id,
                    ),
                )

                if r["title"] and r["title"] != old_title:
                    cursor.execute(
                        "UPDATE teacher_role_history SET end_date = date(?, '-1 day') WHERE teacher_id = ? AND record_type = 'TITLE' AND end_date IS NULL",
                        (now_str[:10], t_id),
                    )
                    cursor.execute(
                        "INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (?, 'TITLE', ?, ?)",
                        (t_id, r["title"], now_str[:10]),
                    )

    cursor.execute(
        """
        UPDATE import_batches 
        SET status = 'approved', decided_at = ?, decided_by = ?
        WHERE id = ?
    """,
        (now_str, decided_by, batch_id),
    )

    cursor.execute("DELETE FROM staging_teachers WHERE batch_id = ?", (batch_id,))
    conn.commit()

    # 4. Verify results
    cursor.execute("SELECT * FROM teachers WHERE name = 'Nguyễn Văn New'")
    new_gv = cursor.fetchone()
    assert new_gv is not None
    assert new_gv["id"] == 9999
    assert float(new_gv["salary_coefficient"]) == 4.4

    # Verify title updated to "Giáo sư" for Nguyễn Văn A
    cursor.execute(
        """
        SELECT value_text FROM teacher_role_history 
        WHERE teacher_id = ? AND record_type = 'TITLE' 
        ORDER BY start_date DESC LIMIT 1
    """,
        (t_a["id"],),
    )
    title_row = cursor.fetchone()
    assert title_row["value_text"] == "Giáo sư"

    # Verify staging rows are deleted
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM staging_teachers WHERE batch_id = ?", (batch_id,)
    )
    assert cursor.fetchone()["cnt"] == 0

    conn.close()


def test_approval_workflow_activities(tmp_path):
    test_db = os.path.join(tmp_path, "test_approval_act.sqlite")
    os.environ["DB_PATH"] = test_db

    init_db()
    seed_initial_data()

    import seed_teachers

    seed_teachers.run()

    conn = get_connection()
    cursor = conn.cursor()

    # Verify Nguyễn Văn A exists
    cursor.execute("SELECT id FROM teachers WHERE name = 'Nguyễn Văn A'")
    t_a = cursor.fetchone()
    assert t_a is not None

    # Retrieve or create timeframe
    cursor.execute("SELECT id FROM timeframes WHERE name = 'Năm học 2025-2026'")
    tf_row = cursor.fetchone()
    if tf_row:
        tf_id = tf_row[0]
    else:
        cursor.execute(
            "INSERT INTO timeframes (name, start_date, end_date) VALUES ('Năm học 2025-2026', '2025-09-01', '2026-06-30')"
        )
        tf_id = cursor.lastrowid

    # Retrieve or create activity type
    cursor.execute("SELECT id FROM activity_types WHERE name = 'Đọc sách'")
    act_row = cursor.fetchone()
    if act_row:
        act_id = act_row[0]
    else:
        cursor.execute(
            "INSERT INTO activity_types (name, category, unit, base_conversion_rate) VALUES ('Đọc sách', 'Khác', 'Giờ', 1.0)"
        )
        act_id = cursor.lastrowid

    # Create pending batch
    cursor.execute("""
        INSERT INTO import_batches (domain, dept_name, uploaded_by, filename, row_count, status)
        VALUES ('activities', 'Khoa CNTT', 'test_user', 'logs.xlsx', 1, 'pending')
    """)
    batch_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO staging_activities (
            batch_id, row_num, teacher_name, activity_type_name, log_date, quantity,
            class_level, class_type, student_count, nckh_level, is_main_author,
            is_foreign_language_instruction, note, timeframe_name, diff_marker, diff_detail
        ) VALUES (?, 1, 'Nguyễn Văn A', 'Đọc sách', '2025-10-10', 5.0, NULL, NULL, 0, NULL, 1, 0, 'Đọc tại thư viện', 'Năm học 2025-2026', 'NEW', '')
    """,
        (batch_id,),
    )

    conn.commit()

    # Run the approval code
    cursor.execute("SELECT * FROM staging_activities WHERE batch_id = ?", (batch_id,))
    staging_rows = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, name FROM timeframes")
    tf_map = {row["name"].strip().lower(): row["id"] for row in cursor.fetchall()}
    cursor.execute("SELECT id, name FROM teachers")
    t_map = {row["name"].strip().lower(): row["id"] for row in cursor.fetchall()}
    cursor.execute("SELECT * FROM activity_types")
    act_map = {row["name"].strip().lower(): row["id"] for row in cursor.fetchall()}

    for r in staging_rows:
        if r["diff_marker"] == "NEW":
            t_id = t_map.get(str(r["teacher_name"]).strip().lower())
            tf_id_m = tf_map.get(str(r["timeframe_name"]).strip().lower())
            act_id_m = act_map.get(str(r["activity_type_name"]).strip().lower())

            if t_id and tf_id_m and act_id_m:
                cursor.execute("SELECT * FROM activity_types WHERE id = ?", (act_id_m,))
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

                conv_hours = calculate_activity_hours(log_row_dict, dict(act_row))

                cursor.execute(
                    """
                    INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity, class_level, class_type, student_count, nckh_level, is_main_author, is_foreign_language_instruction, note, timeframe_id, converted_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        t_id,
                        act_id_m,
                        r["log_date"],
                        r["quantity"],
                        r["class_level"],
                        r["class_type"],
                        r["student_count"],
                        r["nckh_level"],
                        r["is_main_author"],
                        r["is_foreign_language_instruction"],
                        r["note"],
                        tf_id_m,
                        conv_hours,
                    ),
                )

    cursor.execute(
        "UPDATE import_batches SET status = 'approved' WHERE id = ?", (batch_id,)
    )
    cursor.execute("DELETE FROM staging_activities WHERE batch_id = ?", (batch_id,))
    conn.commit()

    # Verify log was created
    cursor.execute("SELECT * FROM activity_logs WHERE teacher_id = ?", (t_a["id"],))
    log = cursor.fetchone()
    assert log is not None
    assert float(log["converted_hours"]) == 5.0

    conn.close()


def test_approval_workflow_schedule(tmp_path):
    test_db = os.path.join(tmp_path, "test_approval_sch.sqlite")
    os.environ["DB_PATH"] = test_db

    init_db()
    seed_initial_data()

    import seed_teachers

    seed_teachers.run()

    conn = get_connection()
    cursor = conn.cursor()

    # Verify Nguyễn Văn A exists
    cursor.execute("SELECT id FROM teachers WHERE name = 'Nguyễn Văn A'")
    t_a = cursor.fetchone()
    assert t_a is not None

    # Retrieve or create timeframe
    cursor.execute("SELECT id FROM timeframes WHERE name = 'Năm học 2025-2026'")
    tf_row = cursor.fetchone()
    if tf_row:
        tf_id = tf_row[0]
    else:
        cursor.execute(
            "INSERT INTO timeframes (name, start_date, end_date) VALUES ('Năm học 2025-2026', '2025-09-01', '2026-06-30')"
        )
        tf_id = cursor.lastrowid

    # Create pending batch
    cursor.execute("""
        INSERT INTO import_batches (domain, dept_name, uploaded_by, filename, row_count, status)
        VALUES ('schedule', 'Khoa CNTT', 'test_user', 'sch.xlsx', 1, 'pending')
    """)
    batch_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO staging_schedule (
            batch_id, row_num, teacher_name, subject_name, loai, nhom, si_so,
            tiet_quy_doi, he_so_tin_chi, he_so_lop_dong, tiet_thuc_day, timeframe_name, diff_marker, diff_detail
        ) VALUES (?, 1, 'Nguyễn Văn A', 'Toán Cao Cấp', 'Lý thuyết', 'Nhóm 1', 40, 45.0, 1.0, 1.0, 45.0, 'Năm học 2025-2026', 'NEW', '')
    """,
        (batch_id,),
    )

    conn.commit()

    # Run approval
    cursor.execute("SELECT * FROM staging_schedule WHERE batch_id = ?", (batch_id,))
    staging_rows = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, name FROM timeframes")
    tf_map = {row["name"].strip().lower(): row["id"] for row in cursor.fetchall()}
    cursor.execute("SELECT id, name FROM teachers")
    t_map = {row["name"].strip().lower(): row["id"] for row in cursor.fetchall()}

    for r in staging_rows:
        tf_id_m = tf_map.get(str(r["timeframe_name"]).strip().lower())
        t_id = t_map.get(str(r["teacher_name"]).strip().lower())

        if t_id and tf_id_m and r["diff_marker"] == "NEW":
            cursor.execute(
                """
                INSERT INTO bulk_teaching_assignments (timeframe_id, teacher_id, subject_name, loai, nhom, si_so, tiet_quy_doi, he_so_tin_chi, ghi_chu, he_so_lop_dong, tiet_thuc_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    tf_id_m,
                    t_id,
                    r["subject_name"],
                    r["loai"],
                    r["nhom"],
                    r["si_so"],
                    r["tiet_quy_doi"],
                    r["he_so_tin_chi"],
                    "",
                    r["he_so_lop_dong"],
                    r["tiet_thuc_day"],
                ),
            )

    cursor.execute(
        "UPDATE import_batches SET status = 'approved' WHERE id = ?", (batch_id,)
    )
    cursor.execute("DELETE FROM staging_schedule WHERE batch_id = ?", (batch_id,))
    conn.commit()

    # Verify assignment was created
    cursor.execute(
        "SELECT * FROM bulk_teaching_assignments WHERE teacher_id = ?", (t_a["id"],)
    )
    assign = cursor.fetchone()
    assert assign is not None
    assert assign["subject_name"] == "Toán Cao Cấp"

    conn.close()
