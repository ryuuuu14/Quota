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
        is_female BOOLEAN DEFAULT 0
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
        
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        unit TEXT NOT NULL,
        base_conversion_rate REAL NOT NULL,
        is_teaching_activity BOOLEAN DEFAULT 0,
        is_nckh_activity BOOLEAN DEFAULT 0
    )
    ''')
    
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
    
    conn.commit()
    conn.close()

def seed_initial_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO settings (key, value, description) VALUES ('total_yearly_hours', '1760', 'Tổng thời gian hành chính trong năm')")
        cursor.execute("INSERT INTO settings (key, value, description) VALUES ('admin_to_teaching_ratio', '3', '3 giờ hành chính = 1 giờ chuẩn')")
        cursor.execute("INSERT INTO settings (key, value, description) VALUES ('standard_academic_weeks', '44', 'Số tuần tiêu chuẩn trong một năm học')")
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

    # Reductions and Activities are seeded via separate scripts (seed_reductions.py, seed_activities.py)
    pass
            
    conn.commit()
    conn.close()

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

def delete_teacher(teacher_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activity_logs WHERE teacher_id = ?", (teacher_id,))
    cursor.execute("DELETE FROM teacher_role_history WHERE teacher_id = ?", (teacher_id,))
    cursor.execute("DELETE FROM manual_conversions WHERE teacher_id = ?", (teacher_id,))
    cursor.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    seed_initial_data()
    print("DB created. Data seeded.")
