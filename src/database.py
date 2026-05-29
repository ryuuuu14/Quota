import sqlite3
import os

# Always resolve DB relative to project root, never to CWD
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_default_db = os.path.join(_project_root, 'data', 'database.sqlite')
DB_PATH = os.environ.get('DB_PATH', _default_db)

# Ensure parent directory exists so no silent fallback to wrong path
_db_dir = os.path.dirname(os.path.abspath(DB_PATH))
if not os.path.exists(_db_dir):
    os.makedirs(_db_dir, exist_ok=True)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT NOT NULL,
        description TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS timeframes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        norm_multiplier REAL DEFAULT 1.0,
        standard_academic_weeks REAL DEFAULT 44.0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        name TEXT PRIMARY KEY,
        is_teaching_dept BOOLEAN DEFAULT 1
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS titles (
        name TEXT PRIMARY KEY,
        base_teaching_hours_natural INTEGER NOT NULL,
        base_teaching_hours_social INTEGER NOT NULL,
        base_nckh_hours INTEGER NOT NULL DEFAULT 600
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reduction_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        rule_type TEXT NOT NULL,
        teaching_reduction_pct REAL NOT NULL DEFAULT 0.0,
        nckh_reduction_pct REAL NOT NULL DEFAULT 0.0,
        condition_note TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        subject_group TEXT NOT NULL,
        is_female BOOLEAN DEFAULT 0,
        employment_type TEXT DEFAULT 'TEACHER',
        guest_rank TEXT,
        total_12m_salary REAL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teacher_role_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        record_type TEXT NOT NULL,
        value_text TEXT,
        reduction_rule_id INTEGER,
        start_date DATE NOT NULL,
        end_date DATE,
        actual_weeks_override REAL,
        FOREIGN KEY(teacher_id) REFERENCES teachers(id),
        FOREIGN KEY(reduction_rule_id) REFERENCES reduction_rules(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS academic_holidays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timeframe_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        FOREIGN KEY(timeframe_id) REFERENCES timeframes(id)
    )
    ''')
    
    # Run migrations for existing database
    try:
        cursor.execute("ALTER TABLE teacher_role_history ADD COLUMN actual_weeks_override REAL")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE timeframes ADD COLUMN standard_academic_weeks REAL DEFAULT 44.0")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE teachers ADD COLUMN employment_type TEXT DEFAULT 'TEACHER'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE teachers ADD COLUMN guest_rank TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE teachers ADD COLUMN total_12m_salary REAL")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE teachers ADD COLUMN police_rank_id INTEGER REFERENCES police_ranks(id)")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE teachers ADD COLUMN salary_coefficient REAL")
    except sqlite3.OperationalError:
        pass
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        unit TEXT NOT NULL,
        base_conversion_rate REAL NOT NULL,
        is_teaching_activity BOOLEAN DEFAULT 0,
        is_nckh_activity BOOLEAN DEFAULT 0,
        applicable_employment_types TEXT DEFAULT 'ALL'
    )
    ''')
    
    try:
        cursor.execute("ALTER TABLE activity_types ADD COLUMN applicable_employment_types TEXT DEFAULT 'ALL'")
    except sqlite3.OperationalError:
        pass
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER,
        activity_type_id INTEGER,
        log_date DATE NOT NULL,
        quantity REAL NOT NULL,
        
        class_level TEXT,
        class_type TEXT,
        student_count INTEGER DEFAULT 0,
        
        nckh_level TEXT,
        is_main_author BOOLEAN DEFAULT 1,
        is_foreign_language_instruction BOOLEAN DEFAULT 0,
        
        converted_hours REAL NOT NULL,
        note TEXT,
        timeframe_id INTEGER,
        FOREIGN KEY(teacher_id) REFERENCES teachers(id),
        FOREIGN KEY(activity_type_id) REFERENCES activity_types(id),
        FOREIGN KEY(timeframe_id) REFERENCES timeframes(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payroll_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        timeframe_id INTEGER NOT NULL,
        task_type TEXT NOT NULL,
        quantity REAL NOT NULL,
        amount_vnd REAL NOT NULL,
        log_date DATE NOT NULL,
        FOREIGN KEY(teacher_id) REFERENCES teachers(id),
        FOREIGN KEY(timeframe_id) REFERENCES timeframes(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS manual_conversions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        timeframe_id INTEGER NOT NULL,
        from_category TEXT NOT NULL,
        to_category TEXT NOT NULL,
        from_amount REAL NOT NULL,
        to_amount REAL NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(teacher_id) REFERENCES teachers(id),
        FOREIGN KEY(timeframe_id) REFERENCES timeframes(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS police_ranks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        rank_name   TEXT NOT NULL UNIQUE,
        coefficient REAL NOT NULL,
        rank_group  TEXT NOT NULL DEFAULT 'SI_QUAN',
        sort_order  INTEGER NOT NULL DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS session_teacher_totals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timeframe_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        giang_day_truc_tiep REAL NOT NULL DEFAULT 0.0,
        hdcm_bd REAL NOT NULL DEFAULT 0.0,
        nckh_total REAL NOT NULL DEFAULT 0.0,
        nvk_total REAL NOT NULL DEFAULT 0.0,
        UNIQUE(timeframe_id, teacher_id),
        FOREIGN KEY(timeframe_id) REFERENCES timeframes(id),
        FOREIGN KEY(teacher_id) REFERENCES teachers(id)
    )
    ''')

    # Migration: teacher_rank_history (added in Phase 4)
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teacher_rank_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            police_rank_id INTEGER NOT NULL,
            salary_coefficient REAL NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            note TEXT,
            FOREIGN KEY(teacher_id) REFERENCES teachers(id),
            FOREIGN KEY(police_rank_id) REFERENCES police_ranks(id)
        )
        ''')
    except Exception:
        pass

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bulk_teaching_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timeframe_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        subject_name TEXT NOT NULL,
        loai TEXT NOT NULL,
        nhom TEXT DEFAULT '',
        si_so INTEGER NOT NULL,
        tiet_quy_doi REAL NOT NULL,
        he_so_tin_chi REAL NOT NULL DEFAULT 1.0,
        ghi_chu TEXT DEFAULT '',
        he_so_lop_dong REAL NOT NULL,
        tiet_thuc_day REAL NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(timeframe_id) REFERENCES timeframes(id),
        FOREIGN KEY(teacher_id) REFERENCES teachers(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bulk_import_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timeframe_id INTEGER NOT NULL UNIQUE,
        filename TEXT NOT NULL,
        file_blob BLOB NOT NULL,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(timeframe_id) REFERENCES timeframes(id)
    )
    ''')

    conn.commit()
    conn.close()

def seed_initial_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO settings (key, value, description) VALUES ('total_yearly_hours', '1760', 'Tổng thời gian hành chính trong năm')")
        cursor.execute("INSERT INTO settings (key, value, description) VALUES ('admin_to_teaching_ratio', '3', '3 giờ hành chính = 1 giờ chuẩn')")
        cursor.execute("INSERT INTO settings (key, value, description) VALUES ('standard_academic_weeks', '44', 'Số tuần tiêu chuẩn trong một năm học')")
        cursor.execute("INSERT INTO settings (key, value, description) VALUES ('base_salary', '2340000', 'Lương cơ sở (VNĐ/tháng) — NĐ 73/2024/NĐ-CP')")
    except: pass
        
    try:
        cursor.execute("INSERT INTO timeframes (name, start_date, end_date, norm_multiplier, standard_academic_weeks) VALUES ('Năm học 2025-2026', '2025-09-01', '2026-07-06', 1.0, 44.0)")
    except: pass

    # Seed Titles - Dựa trên quy định Điều 6
    titles = [
        ('Giáo sư, Phó Giáo sư', 330, 310, 600),
        ('Giảng viên chính', 300, 280, 600),
        ('Giảng viên', 270, 250, 600),
        ('Trợ giảng', 240, 200, 300)
    ]
    for t in titles:
        try: cursor.execute("INSERT INTO titles (name, base_teaching_hours_natural, base_teaching_hours_social, base_nckh_hours) VALUES (?, ?, ?, ?)", t)
        except: pass

    # Seed Departments
    departments = [
        ('Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học', 1),
        ('Nhà giáo giảng dạy thực hành', 1),
        ('Chính trị, Pháp luật, Nghiệp vụ', 1),
        ('Công tác tại phòng, trung tâm', 0)
    ]
    for d in departments:
        try: cursor.execute("INSERT INTO departments (name, is_teaching_dept) VALUES (?, ?)", d)
        except: pass

    seed_police_ranks(conn, cursor)

    # Reductions and Activities are seeded via separate scripts (seed_reductions.py, seed_activities.py)
    pass
            
    conn.commit()
    conn.close()

def seed_police_ranks(conn, cursor):
    ranks = [
        # Sĩ quan cấp tướng (Bảng 6, NĐ 204/2004/NĐ-CP)
        ('Đại tướng', 10.40, 'SI_QUAN', 1),
        ('Thượng tướng', 9.80, 'SI_QUAN', 2),
        ('Trung tướng', 9.20, 'SI_QUAN', 3),
        ('Thiếu tướng', 8.60, 'SI_QUAN', 4),
        # Sĩ quan cấp tá
        ('Đại tá', 8.00, 'SI_QUAN', 5),
        ('Thượng tá', 7.30, 'SI_QUAN', 6),
        ('Trung tá', 6.60, 'SI_QUAN', 7),
        ('Thiếu tá', 6.00, 'SI_QUAN', 8),
        # Sĩ quan cấp úy
        ('Đại úy', 5.40, 'SI_QUAN', 9),
        ('Thượng úy', 5.00, 'SI_QUAN', 10),
        ('Trung úy', 4.60, 'SI_QUAN', 11),
        ('Thiếu úy', 4.20, 'SI_QUAN', 12),
        # Hạ sĩ quan
        ('Thượng sĩ', 3.80, 'HA_SI_QUAN', 13),
        ('Trung sĩ', 3.50, 'HA_SI_QUAN', 14),
        ('Hạ sĩ', 3.20, 'HA_SI_QUAN', 15),
        # Chuyên môn kỹ thuật — Nhóm 1 (ĐH)
        ('CMKT Nhóm 1 (Bậc 1)', 3.50, 'CMKT_NHOM1', 16),
        ('CMKT Nhóm 1 (Bậc 2)', 4.05, 'CMKT_NHOM1', 17),
        ('CMKT Nhóm 1 (Bậc 3)', 4.60, 'CMKT_NHOM1', 18),
        ('CMKT Nhóm 1 (Bậc 4)', 5.15, 'CMKT_NHOM1', 19),
        ('CMKT Nhóm 1 (Bậc 5)', 5.70, 'CMKT_NHOM1', 20),
        ('CMKT Nhóm 1 (Bậc 6)', 6.25, 'CMKT_NHOM1', 21),
        ('CMKT Nhóm 1 (Bậc 7)', 6.65, 'CMKT_NHOM1', 22),
        # Chuyên môn kỹ thuật — Nhóm 2 (CĐ)
        ('CMKT Nhóm 2 (Bậc 1)', 3.20, 'CMKT_NHOM2', 23),
        ('CMKT Nhóm 2 (Bậc 2)', 3.75, 'CMKT_NHOM2', 24),
        ('CMKT Nhóm 2 (Bậc 3)', 4.30, 'CMKT_NHOM2', 25),
        ('CMKT Nhóm 2 (Bậc 4)', 4.85, 'CMKT_NHOM2', 26),
        ('CMKT Nhóm 2 (Bậc 5)', 5.40, 'CMKT_NHOM2', 27),
        ('CMKT Nhóm 2 (Bậc 6)', 5.95, 'CMKT_NHOM2', 28),
        ('CMKT Nhóm 2 (Bậc 7)', 6.35, 'CMKT_NHOM2', 29),
    ]
    for rank_name, coefficient, rank_group, sort_order in ranks:
        try:
            cursor.execute("""
                INSERT INTO police_ranks (rank_name, coefficient, rank_group, sort_order)
                VALUES (?, ?, ?, ?)
            """, (rank_name, coefficient, rank_group, sort_order))
        except:
            pass
    conn.commit()

def seed_academic_holidays():
    """
    Placeholder for ad-hoc holiday modifications during the year.
    academic_holidays stores only UNEXPECTED changes/closures
    (e.g. storm days, additional closures).
    Standard holidays (Tet, Sep 2, Apr 30+May 1, summer break)
    are BUILT INTO the timeframe date range as the "year remainder"
    (weekdays beyond 44 weeks = operational buffer).
    
    To add a modification: INSERT INTO academic_holidays
    (timeframe_id, name, start_date, end_date) VALUES (?, ?, ?, ?)
    """
    pass

def get_base_salary(cursor=None):
    """Get base salary from settings, default 2,340,000 VND."""
    close_on_exit = False
    if cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        close_on_exit = True
    cursor.execute("SELECT value FROM settings WHERE key = 'base_salary'")
    row = cursor.fetchone()
    result = float(row['value']) if row else 2340000.0
    if close_on_exit:
        conn.close()
    return result

def compute_total_12m_salary(salary_coefficient, base_salary=None):
    """Compute annual salary from coefficient × base_salary × 12.
    Returns None if coefficient is None/0 (fallback to manual total_12m_salary)."""
    if not salary_coefficient or salary_coefficient <= 0:
        return None
    if base_salary is None:
        base_salary = get_base_salary()
    return salary_coefficient * base_salary * 12

def get_police_ranks(cursor=None):
    """Return all police ranks sorted by rank_group, sort_order."""
    close_on_exit = False
    if cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        close_on_exit = True
    cursor.execute("SELECT id, rank_name, coefficient, rank_group FROM police_ranks ORDER BY sort_order")
    rows = cursor.fetchall()
    if close_on_exit:
        conn.close()
    return [dict(r) for r in rows]

def get_teacher_rank_history(teacher_id, cursor=None):
    """Get rank history for a teacher, ordered by start_date."""
    close_on_exit = False
    if cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        close_on_exit = True
    cursor.execute("""
        SELECT rh.id, rh.teacher_id, rh.police_rank_id, rh.salary_coefficient,
               rh.start_date, rh.end_date, rh.note, pr.rank_name
        FROM teacher_rank_history rh
        JOIN police_ranks pr ON rh.police_rank_id = pr.id
        WHERE rh.teacher_id = ?
        ORDER BY rh.start_date ASC
    """, (teacher_id,))
    rows = cursor.fetchall()
    if close_on_exit:
        conn.close()
    return [dict(r) for r in rows]

def compute_pro_rata_salary(teacher_id, timeframe_id):
    """Compute total_12m_salary with pro-rata for rank changes during a timeframe.
    Returns (total_12m, details) where details is a list of segment descriptions."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT start_date, end_date FROM timeframes WHERE id = ?", (timeframe_id,))
    tf = cur.fetchone()
    if not tf:
        conn.close()
        return None, ["Timeframe not found"]
    tf_start, tf_end = tf['start_date'], tf['end_date']
    cur.execute("SELECT start_date, end_date FROM academic_holidays WHERE timeframe_id = ?", (timeframe_id,))
    holidays = {r['start_date']: r['end_date'] for r in cur.fetchall()}
    cur.execute("SELECT salary_coefficient FROM teachers WHERE id = ?", (teacher_id,))
    teacher = cur.fetchone()
    if not teacher:
        conn.close()
        return None, ["Teacher not found"]
    current_coeff = teacher['salary_coefficient']
    if not current_coeff:
        conn.close()
        return None, ["No salary coefficient set"]
    rank_changes = get_teacher_rank_history(teacher_id, cur)
    changes_in_tf = [r for r in rank_changes if r['start_date'] <= tf_end and (r['end_date'] is None or r['end_date'] >= tf_start)]
    base_salary = get_base_salary(cur)
    rank_annual = current_coeff * base_salary * 12
    if not changes_in_tf:
        conn.close()
        return rank_annual, [f"Hệ số {current_coeff} x {base_salary} x 12 = {rank_annual:,.0f} đ"]
    total_days = _count_working_days(tf_start, tf_end, holidays)
    if total_days <= 0:
        conn.close()
        return rank_annual, [f"Cảnh báo: timeframe 0 ngày, dùng lương hiện tại {rank_annual:,.0f} đ"]
    segments = []
    seg_starts = sorted(set(
        [tf_start] + [r['start_date'] for r in changes_in_tf if tf_start <= r['start_date'] <= tf_end] +
        [r['end_date'] for r in changes_in_tf if r['end_date'] and tf_start <= r['end_date'] <= tf_end]
    ))
    if seg_starts[-1] != tf_end:
        seg_starts.append(tf_end)
    pro_rata_total = 0.0
    details = []
    for i in range(len(seg_starts) - 1):
        seg_start = seg_starts[i]
        seg_end = seg_starts[i + 1]
        if seg_start >= seg_end:
            continue
        # Find the rank with the latest start_date that covers this segment
        matching = None
        for r in changes_in_tf:
            if r['start_date'] <= seg_start and (r['end_date'] is None or seg_start < r['end_date']):
                if matching is None or r['start_date'] > matching['start_date']:
                    matching = r
        coeff = matching['salary_coefficient'] if matching else current_coeff
        seg_days = _count_working_days(seg_start, seg_end, holidays)
        if seg_days <= 0:
            continue
        seg_annual = coeff * base_salary * 12 * (seg_days / total_days)
        pro_rata_total += seg_annual
        details.append(f"{seg_start} đến {seg_end}: HS {coeff} × {seg_days}/{total_days} ngày = {seg_annual:,.0f} đ")
    conn.close()
    if pro_rata_total <= 0:
        return rank_annual, [f"Không có ngày làm việc, dùng lương hiện tại {rank_annual:,.0f} đ"]
    return pro_rata_total, details

def _count_working_days(start_date, end_date, holidays):
    """Count weekdays (Mon-Fri) between two dates inclusive, excluding holidays."""
    from datetime import datetime, timedelta
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    count = 0
    d = start
    while d <= end:
        if d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    for h_start, h_end in holidays.items():
        hs = datetime.strptime(h_start, '%Y-%m-%d').date()
        he = datetime.strptime(h_end, '%Y-%m-%d').date()
        overlap_start = max(start, hs)
        overlap_end = min(end, he)
        if overlap_start <= overlap_end:
            d2 = overlap_start
            while d2 <= overlap_end:
                if d2.weekday() < 5:
                    count -= 1
                d2 += timedelta(days=1)
    return max(count, 0)

def delete_teacher(teacher_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session_teacher_totals WHERE teacher_id = ?", (teacher_id,))
    cursor.execute("DELETE FROM activity_logs WHERE teacher_id = ?", (teacher_id,))
    cursor.execute("DELETE FROM teacher_role_history WHERE teacher_id = ?", (teacher_id,))
    cursor.execute("DELETE FROM teacher_rank_history WHERE teacher_id = ?", (teacher_id,))
    cursor.execute("DELETE FROM manual_conversions WHERE teacher_id = ?", (teacher_id,))
    cursor.execute("DELETE FROM payroll_records WHERE teacher_id = ?", (teacher_id,))
    cursor.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    seed_initial_data()
    print("DB created. Data seeded.")
