"""Seed Teachers — All 5 regulation examples from Điều 10 (Bản chuẩn toàn văn).

Seeds:
1. Nguyễn Văn A — Trợ giảng, bổ nhiệm 01/12/2025 (Điều 10.3.a)
2. Trần Văn B — Giảng viên, trưng tập + bồi dưỡng + điều trị (Điều 10.3.b)
3. Phạm Thị C — Giảng viên nữ, thai sản + nuôi con nhỏ (Điều 10.3.c)
4. Lê Văn D — Phó Trưởng khoa → Trưởng khoa, đi thực tế + đi học (Ví dụ 1)
5. Bùi Thị X — Giảng viên → Giảng viên chính, thai sản + đi học (Ví dụ 2)

Also seeds: GV Bình Thường (simple teacher with activity logs for GC/NCKH verification).

Chạy 1 lần duy nhất: python src/seed_full.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

TF_NAME = "Năm học 2025-2026"
TF_START = "2025-08-04"
TF_END = "2026-07-05"
STD_WEEKS = 44.0


def ensure_timeframe(conn, cursor):
    """Update or create the 2025-2026 timeframe with regulation-matching dates."""
    existing = cursor.execute(
        "SELECT id FROM timeframes WHERE name = ?", (TF_NAME,)
    ).fetchone()
    if existing:
        cursor.execute(
            """
            UPDATE timeframes SET start_date = ?, end_date = ?, standard_academic_weeks = ?
            WHERE name = ?
        """,
            (TF_START, TF_END, STD_WEEKS, TF_NAME),
        )
        tf_id = existing[0]
        print(f"  Updated timeframe '{TF_NAME}' ({TF_START} -> {TF_END})")
    else:
        cursor.execute(
            """
            INSERT INTO timeframes (name, start_date, end_date, norm_multiplier, standard_academic_weeks)
            VALUES (?, ?, ?, 1.0, ?)
        """,
            (TF_NAME, TF_START, TF_END, STD_WEEKS),
        )
        tf_id = cursor.lastrowid
        print(f"  Created timeframe '{TF_NAME}' ({TF_START} -> {TF_END})")
    return tf_id


def ensure_settings(conn, cursor):
    settings = [
        ("total_yearly_hours", "1760", "Tổng thời gian hành chính trong năm"),
        ("admin_to_teaching_ratio", "3", "3 giờ hành chính = 1 giờ chuẩn"),
        ("standard_academic_weeks", "44", "Số tuần tiêu chuẩn trong một năm học"),
    ]
    for k, v, d in settings:
        try:
            cursor.execute(
                "INSERT INTO settings (key, value, description) VALUES (?,?,?)",
                (k, v, d),
            )
        except Exception:
            pass


def ensure_titles(conn, cursor):
    titles = [
        ("Giáo sư, Phó Giáo sư", 330, 310, 600),
        ("Giảng viên chính", 300, 280, 600),
        ("Giảng viên", 270, 250, 600),
        ("Trợ giảng", 240, 200, 300),
    ]
    for t in titles:
        cursor.execute(
            "INSERT OR REPLACE INTO titles (name, base_teaching_hours_natural, base_teaching_hours_social, base_nckh_hours) VALUES (?,?,?,?)",
            t,
        )


def ensure_departments(conn, cursor):
    depts = [
        ("Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học", 1),
        ("Nhà giáo giảng dạy thực hành", 1),
        ("Chính trị, Pháp luật, Nghiệp vụ", 1),
        ("Công tác tại phòng, trung tâm", 0),
    ]
    for d in depts:
        try:
            cursor.execute(
                "INSERT INTO departments (name, is_teaching_dept) VALUES (?,?)", d
            )
        except Exception:
            pass


def get_rule_id(cursor, name):
    row = cursor.execute(
        "SELECT id FROM reduction_rules WHERE name = ?", (name,)
    ).fetchone()
    return row[0] if row else None


def get_act_type_id(cursor, name):
    row = cursor.execute(
        "SELECT id FROM activity_types WHERE name = ?", (name,)
    ).fetchone()
    return row[0] if row else None


def ensure_reduction_rules(conn, cursor):
    """Add any rules from seed_reductions that are missing."""
    from seed_reductions import REDUCTIONS

    for r in REDUCTIONS:
        try:
            cursor.execute(
                """
                INSERT INTO reduction_rules (name, rule_type, teaching_reduction_pct, nckh_reduction_pct, condition_note)
                VALUES (?,?,?,?,?)
            """,
                r,
            )
        except Exception:
            pass


def get_police_rank_id(cursor, rank_name):
    row = cursor.execute(
        "SELECT id FROM police_ranks WHERE rank_name = ?", (rank_name,)
    ).fetchone()
    return row[0] if row else None


SUBJECT_GROUP = "Chính trị/Nghiệp vụ"
DEPT_NAME = "Chính trị, Pháp luật, Nghiệp vụ"


def seed_teacher_NguyenVanA(conn, cursor, tf_id):
    """Nguyễn Văn A — Trợ giảng, bổ nhiệm 01/12/2025 (Điều 10.3.a)."""
    print("\n  1. Nguyễn Văn A — Trợ giảng (Điều 10.3.a)")
    subject_group = SUBJECT_GROUP
    pr_id = get_police_rank_id(cursor, "Thiếu úy")
    cursor.execute(
        "INSERT INTO teachers (name, subject_group, is_female, employment_type, total_12m_salary, police_rank_id, salary_coefficient) VALUES (?, ?, ?, 'TEACHER', ?, ?, ?)",
        ("Nguyễn Văn A", subject_group, 0, 85_000_000, pr_id, 4.20),
    )
    tid = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'TITLE', ?, ?, ?)
    """,
        (tid, "Giảng viên", "2025-08-04", "2025-11-30"),
    )

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
        VALUES (?, 'TITLE', ?, ?)
    """,
        (tid, "Trợ giảng", "2025-12-01"),
    )

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'DEPARTMENT', ?, ?, ?)
    """,
        (tid, DEPT_NAME, "2025-08-04", None),
    )

    conn.commit()
    print(f"    teacher_id={tid}")
    return tid


def seed_teacher_TranVanB(conn, cursor, tf_id):
    """Trần Văn B — Giảng viên, trưng tập + bồi dưỡng + điều trị (Điều 10.3.b)."""
    print(
        "\n  2. Trần Văn B — Giảng viên, trưng tập + bồi dưỡng + điều trị (Điều 10.3.b)"
    )
    subject_group = SUBJECT_GROUP
    pr_id = get_police_rank_id(cursor, "Trung úy")
    cursor.execute(
        "INSERT INTO teachers (name, subject_group, is_female, employment_type, total_12m_salary, police_rank_id, salary_coefficient) VALUES (?, ?, ?, 'TEACHER', ?, ?, ?)",
        ("Trần Văn B", subject_group, 0, 95_000_000, pr_id, 4.60),
    )
    tid = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
        VALUES (?, 'TITLE', ?, ?)
    """,
        (tid, "Giảng viên", "2025-08-04"),
    )

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'DEPARTMENT', ?, ?, ?)
    """,
        (tid, DEPT_NAME, "2025-08-04", None),
    )

    # Trưng tập: 01/9/2025 → 28/12/2025 (16 tuần)
    rule_tt = get_rule_id(cursor, "Đi thực tế / Trưng tập (dưới 6 tháng)")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
        VALUES (?, 'REDUCTION', 'Trưng tập', ?, ?, ?)
    """,
        (tid, rule_tt, "2025-09-01", "2025-12-28"),
    )

    # Bồi dưỡng 21 ngày: 27/10/2025 → 17/11/2025 (nằm trong thời gian trưng tập)
    rule_bd = get_rule_id(cursor, "Đi học / Bồi dưỡng (từ 6 đến dưới 10 tháng)")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
        VALUES (?, 'REDUCTION', 'Bồi dưỡng', ?, ?, ?)
    """,
        (tid, rule_bd, "2025-10-27", "2025-11-17"),
    )

    # Điều trị bệnh: 06/4/2026 → 27/4/2026 (3 tuần)
    rule_dt = get_rule_id(cursor, "Điều trị bệnh")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
        VALUES (?, 'REDUCTION', 'Điều trị bệnh', ?, ?, ?)
    """,
        (tid, rule_dt, "2026-04-06", "2026-04-27"),
    )

    conn.commit()
    print(f"    teacher_id={tid}")
    return tid


def seed_teacher_PhamThiC(conn, cursor, tf_id):
    """Phạm Thị C — Giảng viên nữ, thai sản + nuôi con (Điều 10.3.c)."""
    print("\n  3. Phạm Thị C — Giảng viên nữ, thai sản + nuôi con (Điều 10.3.c)")
    subject_group = SUBJECT_GROUP
    pr_id = get_police_rank_id(cursor, "Thượng úy")
    cursor.execute(
        "INSERT INTO teachers (name, subject_group, is_female, employment_type, total_12m_salary, police_rank_id, salary_coefficient) VALUES (?, ?, ?, 'TEACHER', ?, ?, ?)",
        ("Phạm Thị C", subject_group, 1, 90_000_000, pr_id, 5.00),
    )
    tid = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
        VALUES (?, 'TITLE', ?, ?)
    """,
        (tid, "Giảng viên", "2025-08-04"),
    )

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'DEPARTMENT', ?, ?, ?)
    """,
        (tid, DEPT_NAME, "2025-08-04", None),
    )

    # Thai sản: 01/12/2025 → 01/6/2026, actual 23 weeks per Điều 10.3.c (excluding 3 Tết weeks)
    rule_ts = get_rule_id(cursor, "Nữ nghỉ thai sản")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date, actual_weeks_override)
        VALUES (?, 'REDUCTION', 'Nghỉ thai sản', ?, ?, ?, ?)
    """,
        (tid, rule_ts, "2025-12-01", "2026-06-01", 23.0),
    )

    # Nuôi con <12m: 4 weeks (Điều 10.3.c example: 260 GC x 04 tuần x 15%)
    rule_nc = get_rule_id(cursor, "Nữ nuôi con nhỏ dưới 12 tháng")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date, actual_weeks_override)
        VALUES (?, 'REDUCTION', 'Nuôi con nhỏ dưới 12 tháng', ?, ?, ?, ?)
    """,
        (tid, rule_nc, "2026-06-02", "2026-07-05", 4.0),
    )

    conn.commit()
    print(f"    teacher_id={tid}")
    return tid


def seed_teacher_LeVanD(conn, cursor, tf_id):
    """Lê Văn D — Ví dụ 1: Phó Trưởng khoa → Trưởng khoa, đi thực tế + đi học."""
    print("\n  4. Lê Văn D — Ví dụ 1 (Phó TK→TK, đi thực tế + đi học)")
    subject_group = SUBJECT_GROUP
    pr_id = get_police_rank_id(cursor, "Đại úy")
    cursor.execute(
        "INSERT INTO teachers (name, subject_group, is_female, employment_type, total_12m_salary, police_rank_id, salary_coefficient) VALUES (?, ?, ?, 'TEACHER', ?, ?, ?)",
        ("Lê Văn D", subject_group, 0, 130_000_000, pr_id, 5.40),
    )
    tid = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'TITLE', ?, ?, ?)
    """,
        (tid, "Giảng viên chính", "2025-08-04", None),
    )

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'DEPARTMENT', ?, ?, ?)
    """,
        (tid, DEPT_NAME, "2025-08-04", None),
    )

    # Phó Trưởng khoa: weeks 1-17 (04/8 → 30/11/2025)
    rule_ptk = get_rule_id(cursor, "Phó Trưởng khoa")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, reduction_rule_id, start_date, end_date)
        VALUES (?, 'REDUCTION', ?, ?, ?)
    """,
        (tid, rule_ptk, "2025-08-04", "2025-11-30"),
    )

    # Trưởng khoa: weeks 18-44 (01/12/2025 → 05/6/2026)
    rule_tk = get_rule_id(cursor, "Trưởng khoa")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, reduction_rule_id, start_date, end_date)
        VALUES (?, 'REDUCTION', ?, ?, ?)
    """,
        (tid, rule_tk, "2025-12-01", "2026-07-05"),
    )

    # Đi thực tế 8 tuần: 04/8 → 28/9/2025
    rule_dt = get_rule_id(cursor, "Đi thực tế / Trưng tập (dưới 6 tháng)")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
        VALUES (?, 'REDUCTION', 'Đi thực tế', ?, ?, ?)
    """,
        (tid, rule_dt, "2025-08-04", "2025-09-28"),
    )

    # Đi học 3 tuần: 06/4 → 26/4/2026
    rule_dh = get_rule_id(cursor, "Đi học / Bồi dưỡng (từ 6 đến dưới 10 tháng)")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
        VALUES (?, 'REDUCTION', 'Đi học bồi dưỡng', ?, ?, ?)
    """,
        (tid, rule_dh, "2026-04-06", "2026-04-26"),
    )

    conn.commit()
    print(f"    teacher_id={tid}")
    return tid


def seed_teacher_BuiThiX(conn, cursor, tf_id):
    """Bùi Thị X — Ví dụ 2: GV→GVC, thai sản + đi học."""
    print("\n  5. Bùi Thị X — Ví dụ 2 (GV→GVC, thai sản + đi học)")
    subject_group = SUBJECT_GROUP
    pr_id = get_police_rank_id(cursor, "Thượng úy")
    cursor.execute(
        "INSERT INTO teachers (name, subject_group, is_female, employment_type, total_12m_salary, police_rank_id, salary_coefficient) VALUES (?, ?, ?, 'TEACHER', ?, ?, ?)",
        ("Bùi Thị X", subject_group, 1, 100_000_000, pr_id, 5.00),
    )
    tid = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'TITLE', ?, ?, ?)
    """,
        (tid, "Giảng viên", "2025-08-04", "2025-11-16"),
    )

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
        VALUES (?, 'TITLE', ?, ?)
    """,
        (tid, "Giảng viên chính", "2025-11-17"),
    )

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'DEPARTMENT', ?, ?, ?)
    """,
        (tid, DEPT_NAME, "2025-08-04", None),
    )

    # Thai sản 7 tuần: 04/8 → 21/9/2025
    rule_ts = get_rule_id(cursor, "Nữ nghỉ thai sản")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
        VALUES (?, 'REDUCTION', 'Nghỉ thai sản', ?, ?, ?)
    """,
        (tid, rule_ts, "2025-08-04", "2025-09-21"),
    )

    # Nuôi con <12m: 04/8/2025 → 31/3/2026
    rule_nc = get_rule_id(cursor, "Nữ nuôi con nhỏ dưới 12 tháng")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
        VALUES (?, 'REDUCTION', 'Nuôi con nhỏ dưới 12 tháng', ?, ?, ?)
    """,
        (tid, rule_nc, "2025-08-04", "2026-03-31"),
    )

    # Đi học 13 tuần: 06/4 → 05/7/2026 (clipped to TF end in calculation)
    rule_dh = get_rule_id(cursor, "Đi học / Bồi dưỡng (từ 6 đến dưới 10 tháng)")
    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, reduction_rule_id, start_date, end_date)
        VALUES (?, 'REDUCTION', 'Đi học', ?, ?, ?)
    """,
        (tid, rule_dh, "2026-04-06", "2026-07-05"),
    )

    conn.commit()
    print(f"    teacher_id={tid}")
    return tid


def seed_teacher_GVBinhThuong(conn, cursor, tf_id):
    """GV Bình Thường — Simple teacher with activity logs for verification."""
    print("\n  6. GV Bình Thường — Activity log verification")
    subject_group = SUBJECT_GROUP
    pr_id = get_police_rank_id(cursor, "Trung úy")
    cursor.execute(
        "INSERT INTO teachers (name, subject_group, is_female, employment_type, total_12m_salary, police_rank_id, salary_coefficient) VALUES (?, ?, ?, 'TEACHER', ?, ?, ?)",
        ("GV Bình Thường", subject_group, 0, 85_000_000, pr_id, 4.60),
    )
    tid = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
        VALUES (?, 'TITLE', ?, ?)
    """,
        (tid, "Giảng viên", "2025-08-04"),
    )

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'DEPARTMENT', ?, ?, ?)
    """,
        (tid, DEPT_NAME, "2025-08-04", None),
    )

    conn.commit()

    gd_id = get_act_type_id(
        cursor, "GD - Lý thuyết ĐH (dùng class_level+student_count để nhân hệ số)"
    )
    nckh_id = get_act_type_id(cursor, "NCKH - Bài báo ISI/Scopus")
    hdcm_id = get_act_type_id(cursor, "NVK - Coi thi kết thúc HP")

    if gd_id:
        cursor.execute(
            """
            INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity,
                class_level, class_type, student_count, converted_hours, note, timeframe_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                tid,
                gd_id,
                "2025-10-15",
                100.0,
                "Đại học",
                "Lý thuyết",
                40,
                0.0,
                "",
                tf_id,
            ),
        )

    if hdcm_id:
        cursor.execute(
            """
            INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity,
                converted_hours, note, timeframe_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (tid, hdcm_id, "2025-12-20", 10.0, 0.0, "", tf_id),
        )

    if nckh_id:
        cursor.execute(
            """
            INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity,
                nckh_level, is_main_author, converted_hours, note, timeframe_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (tid, nckh_id, "2026-03-01", 1.0, "Quốc gia", 1, 0.0, "", tf_id),
        )

    conn.commit()
    print(f"    teacher_id={tid}")
    return tid


def seed_teacher_GuestSpeaker(conn, cursor, tf_id):
    """Nguyễn Thị Khách — Giảng viên thỉnh giảng (GUEST)."""
    print("\n  7. Nguyễn Thị Khách — Giảng viên thỉnh giảng (GUEST)")
    subject_group = SUBJECT_GROUP
    cursor.execute(
        "INSERT INTO teachers (name, subject_group, is_female, employment_type, guest_rank) VALUES (?, ?, ?, 'GUEST', ?)",
        ("Nguyễn Thị Khách", subject_group, 1, "Giáo sư"),
    )
    tid = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
        VALUES (?, 'TITLE', ?, ?)
    """,
        (tid, "Giáo sư, Phó Giáo sư", "2025-08-04"),
    )

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'DEPARTMENT', ?, ?, ?)
    """,
        (tid, DEPT_NAME, "2025-08-04", None),
    )

    conn.commit()
    print(f"    teacher_id={tid}")
    return tid


def seed_teacher_StaffManager(conn, cursor, tf_id):
    """Trần Văn Quản Lý — Cán bộ quản lý (STAFF)."""
    print("\n  8. Trần Văn Quản Lý — Cán bộ quản lý (STAFF)")
    subject_group = SUBJECT_GROUP
    pr_id = get_police_rank_id(cursor, "Đại tá")
    cursor.execute(
        "INSERT INTO teachers (name, subject_group, is_female, employment_type, total_12m_salary, police_rank_id, salary_coefficient) VALUES (?, ?, ?, 'STAFF', ?, ?, ?)",
        ("Trần Văn Quản Lý", subject_group, 0, 150_000_000, pr_id, 8.00),
    )
    tid = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
        VALUES (?, 'TITLE', ?, ?)
    """,
        (tid, "Giảng viên chính", "2025-08-04"),
    )

    cursor.execute(
        """
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, 'DEPARTMENT', ?, ?, ?)
    """,
        (tid, "Công tác tại phòng, trung tâm", "2025-08-04", None),
    )

    conn.commit()
    print(f"    teacher_id={tid}")
    return tid


def delete_existing_teachers(conn, cursor):
    """Remove existing seeded teachers to allow re-seed."""
    names = [
        "Nguyễn Văn A",
        "Trần Văn B",
        "Phạm Thị C",
        "Lê Văn D",
        "Bùi Thị X",
        "GV Bình Thường",
        "Nguyễn Thị Khách",
        "Trần Văn Quản Lý",
    ]
    for name in names:
        row = cursor.execute(
            "SELECT id FROM teachers WHERE name = ?", (name,)
        ).fetchone()
        if row:
            tid = row[0]
            cursor.execute("DELETE FROM activity_logs WHERE teacher_id = ?", (tid,))
            cursor.execute(
                "DELETE FROM teacher_role_history WHERE teacher_id = ?", (tid,)
            )
            cursor.execute(
                "DELETE FROM manual_conversions WHERE teacher_id = ?", (tid,)
            )
            cursor.execute("DELETE FROM teachers WHERE id = ?", (tid,))
    conn.commit()


def run():
    conn = get_connection()
    cursor = conn.cursor()

    ensure_settings(conn, cursor)
    ensure_titles(conn, cursor)
    ensure_departments(conn, cursor)

    tf_id = ensure_timeframe(conn, cursor)

    # Ensure police_ranks exist before any teacher references them
    from database import seed_police_ranks

    seed_police_ranks(conn, cursor)

    from seed_activities import ACTIVITIES

    added_acts = 0
    for a in ACTIVITIES:
        try:
            cursor.execute(
                """
                INSERT INTO activity_types (name, category, unit, base_conversion_rate, is_teaching_activity, is_nckh_activity, applicable_employment_types)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                a,
            )
            added_acts += 1
        except Exception:
            pass
    if added_acts:
        print(f"  Activity types added: {added_acts}")

    ensure_reduction_rules(conn, cursor)
    conn.commit()

    delete_existing_teachers(conn, cursor)

    print("\nSeeding teacher records from regulation Điều 10 examples:")
    print(f"  Timeframe: {TF_NAME} (id={tf_id})")

    seed_teacher_NguyenVanA(conn, cursor, tf_id)
    seed_teacher_TranVanB(conn, cursor, tf_id)
    seed_teacher_PhamThiC(conn, cursor, tf_id)
    seed_teacher_LeVanD(conn, cursor, tf_id)
    seed_teacher_BuiThiX(conn, cursor, tf_id)
    seed_teacher_GVBinhThuong(conn, cursor, tf_id)
    seed_teacher_GuestSpeaker(conn, cursor, tf_id)
    seed_teacher_StaffManager(conn, cursor, tf_id)

    count = cursor.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
    print(f"\n  Total teachers in DB: {count}")

    from database import DB_PATH
    conn.close()
    print(
        "  Done. Teacher records seeded into:",
        DB_PATH,
    )


if __name__ == "__main__":
    run()
