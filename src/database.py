import sqlite3
import os
import pandas as pd
import streamlit as st

# Always resolve DB relative to project root, never to CWD
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_default_db = os.path.join(_project_root, "data", "database.sqlite")

def _resolve_db_path():
    path = os.environ.get("DB_PATH", _default_db)
    if not os.path.isabs(path):
        path = os.path.join(_project_root, path)
    return path

DB_PATH = _resolve_db_path()

# Ensure parent directory exists so no silent fallback to wrong path
_db_dir = os.path.dirname(DB_PATH)
if not os.path.exists(_db_dir):
    os.makedirs(_db_dir, exist_ok=True)


def get_connection():
    path = _resolve_db_path()
    _db_dir = os.path.dirname(path)
    if not os.path.exists(_db_dir):
        os.makedirs(_db_dir, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False, timeout=30.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn


class ThreadLocalConnectionProxy:
    def __init__(self):
        import threading

        self._local = threading.local()

    @property
    def _conn(self):
        if not hasattr(self._local, "conn"):
            self._local.conn = get_connection()
        return self._local.conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self._conn.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._conn.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        if hasattr(self._local, "conn"):
            try:
                self._local.conn.close()
            except Exception:
                pass
            delattr(self._local, "conn")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT NOT NULL,
        description TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timeframes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        norm_multiplier REAL DEFAULT 1.0,
        standard_academic_weeks REAL DEFAULT 44.0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        name TEXT PRIMARY KEY,
        is_teaching_dept BOOLEAN DEFAULT 1,
        dept_code TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS titles (
        name TEXT PRIMARY KEY,
        base_teaching_hours_natural INTEGER NOT NULL,
        base_teaching_hours_social INTEGER NOT NULL,
        base_nckh_hours INTEGER NOT NULL DEFAULT 600
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reduction_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        rule_type TEXT NOT NULL,
        teaching_reduction_pct REAL NOT NULL DEFAULT 0.0,
        nckh_reduction_pct REAL NOT NULL DEFAULT 0.0,
        condition_note TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS police_ranks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        rank_name   TEXT NOT NULL UNIQUE,
        coefficient REAL NOT NULL,
        rank_group  TEXT NOT NULL DEFAULT 'SI_QUAN',
        sort_order  INTEGER NOT NULL DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        subject_group TEXT NOT NULL,
        is_female BOOLEAN DEFAULT 0,
        employment_type TEXT DEFAULT 'TEACHER',
        guest_rank TEXT,
        total_12m_salary REAL,
        police_rank_id INTEGER REFERENCES police_ranks(id),
        salary_coefficient REAL,
        teacher_code TEXT UNIQUE
    )
    """)

    cursor.execute("""
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
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS academic_holidays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timeframe_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        FOREIGN KEY(timeframe_id) REFERENCES timeframes(id)
    )
    """)

    # Run migrations for existing database
    try:
        cursor.execute("ALTER TABLE teachers ADD COLUMN teacher_code TEXT")
        cursor.execute("UPDATE teachers SET teacher_code = CAST(id AS TEXT) WHERE teacher_code IS NULL")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    # Ensure unique index exists (idempotent)
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_teachers_teacher_code ON teachers(teacher_code)")
        conn.commit()
    except sqlite3.OperationalError:
        pass


    try:
        cursor.execute(
            "ALTER TABLE teacher_role_history ADD COLUMN actual_weeks_override REAL"
        )
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute(
            "ALTER TABLE timeframes ADD COLUMN standard_academic_weeks REAL DEFAULT 44.0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE teachers ADD COLUMN employment_type TEXT DEFAULT 'TEACHER'"
        )
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
        cursor.execute(
            "ALTER TABLE teachers ADD COLUMN police_rank_id INTEGER REFERENCES police_ranks(id)"
        )
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE teachers ADD COLUMN salary_coefficient REAL")
    except sqlite3.OperationalError:
        pass
    cursor.execute("""
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
    """)

    try:
        cursor.execute(
            "ALTER TABLE activity_types ADD COLUMN applicable_employment_types TEXT DEFAULT 'ALL'"
        )
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
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
    """)

    cursor.execute("""
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
    """)

    cursor.execute("""
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
    """)


    cursor.execute("""
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
    """)

    # Migration: teacher_rank_history (added in Phase 4)
    try:
        cursor.execute("""
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
        """)
    except Exception:
        pass

    cursor.execute("""
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
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bulk_import_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timeframe_id INTEGER NOT NULL UNIQUE,
        filename TEXT NOT NULL,
        file_blob BLOB NOT NULL,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(timeframe_id) REFERENCES timeframes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teacher_calculated_totals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timeframe_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        tong_gc_da_thuc_hien REAL NOT NULL DEFAULT 0.0,
        nckh_da_thuc_hien REAL NOT NULL DEFAULT 0.0,
        so_gio_duoc_mien_giam REAL NOT NULL DEFAULT 0.0,
        dinh_muc_gc_phai_thuc_hien REAL NOT NULL DEFAULT 0.0,
        is_override BOOLEAN DEFAULT 1,
        note TEXT,
        UNIQUE(timeframe_id, teacher_id),
        FOREIGN KEY(timeframe_id) REFERENCES timeframes(id),
        FOREIGN KEY(teacher_id) REFERENCES teachers(id)
    )
    """)

    # Migration for departments table
    try:
        cursor.execute("ALTER TABLE departments ADD COLUMN dept_code TEXT")
    except Exception:
        pass

    # Admin Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        role TEXT NOT NULL DEFAULT 'teacher',
        department_name TEXT REFERENCES departments(name),
        teacher_id INTEGER REFERENCES teachers(id)
    )
    """)
    try:
        cursor.execute(
            "ALTER TABLE admin_users ADD COLUMN role TEXT NOT NULL DEFAULT 'teacher'"
        )
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute(
            "ALTER TABLE admin_users ADD COLUMN department_name TEXT REFERENCES departments(name)"
        )
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute(
            "ALTER TABLE admin_users ADD COLUMN teacher_id INTEGER REFERENCES teachers(id)"
        )
    except sqlite3.OperationalError:
        pass

    # Notifications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_dept TEXT,
        target_role TEXT,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        batch_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Import Batches Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS import_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT NOT NULL,
        dept_name TEXT,
        uploaded_by TEXT NOT NULL,
        filename TEXT NOT NULL,
        row_count INTEGER,
        status TEXT DEFAULT 'pending',
        rejection_reason TEXT,
        diff_json TEXT,
        snapshot_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        decided_at DATETIME,
        decided_by TEXT,
        diff_version TEXT,
        remarks TEXT
    )
    """)

    # Migrations for import_batches
    for col in ("diff_version", "remarks"):
        try:
            cursor.execute(f"ALTER TABLE import_batches ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass

    # Staging Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staging_teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER REFERENCES import_batches(id) ON DELETE CASCADE,
        row_num INTEGER,
        diff_marker TEXT,
        diff_detail TEXT,
        validation_errors TEXT,
        teacher_name TEXT,
        subject_group TEXT,
        is_female BOOLEAN DEFAULT 0,
        employment_type TEXT DEFAULT 'TEACHER',
        guest_rank TEXT,
        total_12m_salary REAL,
        police_rank_id INTEGER,
        salary_coefficient REAL,
        title TEXT,
        department TEXT,
        role TEXT,
        teacher_id INTEGER,
        study_leave TEXT,
        field_trip TEXT,
        permitted_leave TEXT,
        teacher_code TEXT,
        role_start_date TEXT,
        title_start_date TEXT
    )
    """)
    try:
        cursor.execute("ALTER TABLE staging_teachers ADD COLUMN role TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE staging_teachers ADD COLUMN teacher_id INTEGER")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE staging_teachers ADD COLUMN role_start_date TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE staging_teachers ADD COLUMN title_start_date TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE staging_teachers ADD COLUMN study_leave TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE staging_teachers ADD COLUMN field_trip TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE staging_teachers ADD COLUMN permitted_leave TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE staging_teachers ADD COLUMN teacher_code TEXT")
    except Exception:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staging_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER REFERENCES import_batches(id) ON DELETE CASCADE,
        row_num INTEGER,
        diff_marker TEXT,
        diff_detail TEXT,
        validation_errors TEXT,
        teacher_name TEXT,
        activity_type_name TEXT,
        log_date DATE,
        quantity REAL,
        class_level TEXT,
        class_type TEXT,
        student_count INTEGER DEFAULT 0,
        nckh_level TEXT,
        is_main_author BOOLEAN DEFAULT 1,
        is_foreign_language_instruction BOOLEAN DEFAULT 0,
        note TEXT,
        timeframe_name TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staging_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER REFERENCES import_batches(id) ON DELETE CASCADE,
        row_num INTEGER,
        diff_marker TEXT,
        diff_detail TEXT,
        validation_errors TEXT,
        teacher_name TEXT,
        subject_name TEXT,
        loai TEXT,
        nhom TEXT DEFAULT '',
        si_so INTEGER,
        tiet_quy_doi REAL,
        he_so_tin_chi REAL DEFAULT 1.0,
        he_so_lop_dong REAL,
        tiet_thuc_day REAL,
        timeframe_name TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staging_aggregate_totals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER REFERENCES import_batches(id) ON DELETE CASCADE,
        row_num INTEGER,
        diff_marker TEXT,
        diff_detail TEXT,
        validation_errors TEXT,
        teacher_name TEXT,
        tong_gc_da_thuc_hien REAL,
        nckh_da_thuc_hien REAL,
        so_gio_duoc_mien_giam REAL,
        dinh_muc_gc_phai_thuc_hien REAL,
        note TEXT,
        timeframe_name TEXT
    )
    """)

    # ── Performance indexes ──
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_activity_logs_tf ON activity_logs(timeframe_id)",
        "CREATE INDEX IF NOT EXISTS idx_activity_logs_teacher_tf ON activity_logs(teacher_id, timeframe_id)",
        "CREATE INDEX IF NOT EXISTS idx_teacher_role_history_teacher_tf ON teacher_role_history(teacher_id)",
        # Composite index for correlated subqueries: WHERE teacher_id=? AND record_type=? ORDER BY start_date DESC LIMIT 1
        "CREATE INDEX IF NOT EXISTS idx_teacher_role_history_lookup ON teacher_role_history(teacher_id, record_type, start_date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_manual_conversions_teacher_tf ON manual_conversions(teacher_id, timeframe_id)",
        "CREATE INDEX IF NOT EXISTS idx_session_totals_tf ON session_teacher_totals(timeframe_id)",
        "CREATE INDEX IF NOT EXISTS idx_calculated_totals_tf ON teacher_calculated_totals(timeframe_id)",
        # Composite for is_override queries: WHERE timeframe_id=? AND is_override=1
        "CREATE INDEX IF NOT EXISTS idx_calculated_totals_override ON teacher_calculated_totals(timeframe_id, is_override)",
        # For pending batch count and filtered listing: WHERE status=?
        "CREATE INDEX IF NOT EXISTS idx_import_batches_status ON import_batches(status, created_at DESC)",
        # For bulk_teaching_assignments by timeframe (used in diff_schedule)
        "CREATE INDEX IF NOT EXISTS idx_bulk_assignments_tf ON bulk_teaching_assignments(timeframe_id)",
    ]:
        cursor.execute(idx_sql)

    conn.commit()
    conn.close()

    # Run cleanup of old staging batches/records (older than 30 days)
    cleanup_old_batches()


def cleanup_old_batches():
    """
    Dọn dẹp các lô nhập dữ liệu tạm thời (staging batches/records) cũ hơn 30 ngày và đã được xử lý (không ở trạng thái pending).
    """
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, domain FROM import_batches WHERE status != 'pending' AND created_at < datetime('now', '-30 days')"
            )
            batches_to_delete = cursor.fetchall()

            if batches_to_delete:
                batch_ids = [row[0] for row in batches_to_delete]
                for b_id, domain in batches_to_delete:
                    if domain in (
                        "teachers",
                        "activities",
                        "schedule",
                        "aggregate_totals",
                    ):
                        staging_table = f"staging_{domain}"
                        try:
                            cursor.execute(
                                f"DELETE FROM {staging_table} WHERE batch_id = ?",
                                (b_id,),
                            )
                        except Exception:
                            pass

                placeholders = ",".join("?" for _ in batch_ids)
                cursor.execute(
                    f"DELETE FROM import_batches WHERE id IN ({placeholders})",
                    batch_ids,
                )
    except Exception as e:
        print(f"Error during cleanup of old batches: {e}")
    finally:
        conn.close()


def seed_initial_data():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO settings (key, value, description) VALUES ('total_yearly_hours', '1760', 'Tổng thời gian hành chính trong năm')"
        )
        cursor.execute(
            "INSERT INTO settings (key, value, description) VALUES ('admin_to_teaching_ratio', '3', '3 giờ hành chính = 1 giờ chuẩn')"
        )
        cursor.execute(
            "INSERT INTO settings (key, value, description) VALUES ('standard_academic_weeks', '44', 'Số tuần tiêu chuẩn trong một năm học')"
        )
        cursor.execute(
            "INSERT INTO settings (key, value, description) VALUES ('base_salary', '2340000', 'Lương cơ sở (VNĐ/tháng) — NĐ 73/2024/NĐ-CP')"
        )
    except Exception:
        pass
    try:
        cursor.execute(
            "INSERT INTO settings (key, value, description) VALUES ('nckh_to_gc_ratio', '3.0', 'Tỷ lệ quy đổi NCKH sang Giảng dạy (số giờ NCKH cần để bù 1 giờ GC)')"
        )
        cursor.execute(
            "INSERT INTO settings (key, value, description) VALUES ('gc_to_nckh_ratio', '3.0', 'Tỷ lệ quy đổi Giảng dạy sang NCKH (số giờ NCKH nhận được từ 1 giờ GC bù)')"
        )
        cursor.execute(
            "INSERT INTO settings (key, value, description) VALUES ('min_direct_teaching_ratio', '0.50', 'Tỷ lệ giảng dạy trực tiếp tối thiểu để được bù (Điều 3.6)')"
        )
        cursor.execute(
            "INSERT INTO settings (key, value, description) VALUES ('min_nckh_ratio', '0.25', 'Tỷ lệ hoàn thành NCKH tối thiểu để được quy đổi GC bù (Điều 12.2)')"
        )
    except Exception:
        pass
    try:
        cursor.execute(
            "INSERT INTO timeframes (name, start_date, end_date, norm_multiplier, standard_academic_weeks) VALUES ('Năm học 2025-2026', '2025-08-04', '2026-07-06', 1.0, 44.0)"
        )
        tf_id = cursor.lastrowid
        seed_holidays_for_timeframe(
            conn, tf_id, "Năm học 2025-2026", "2025-08-04", "2026-07-06"
        )
    except Exception:
        pass
    # Seed Titles - Dựa trên quy định Điều 6
    titles = [
        ("Giáo sư, Phó Giáo sư", 330, 310, 600),
        ("Giảng viên chính", 300, 280, 600),
        ("Giảng viên", 270, 250, 600),
        ("Trợ giảng", 240, 200, 300),
    ]
    for t in titles:
        try:
            cursor.execute(
                "INSERT INTO titles (name, base_teaching_hours_natural, base_teaching_hours_social, base_nckh_hours) VALUES (?, ?, ?, ?)",
                t,
            )
        except Exception:
            pass
    # Seed Departments — Legacy generic categories (backward compat with existing calcs/tests)
    legacy_departments = [
        ("Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học", 1, "1111"),
        ("Nhà giáo giảng dạy thực hành", 1, "2222"),
        ("Chính trị, Pháp luật, Nghiệp vụ", 1, "3333"),
        ("Công tác tại phòng, trung tâm", 0, "4444"),
    ]
    # Official departments of Trường Đại học An ninh nhân dân
    official_departments = [
        ("Ban Giám hiệu", 0, "BGH"),
        # 12 Khoa (teaching)
        ("Khoa Lý luận chính trị và Khoa học xã hội nhân văn", 1, "K1"),
        ("Khoa Luật", 1, "K2"),
        ("Khoa Nghiệp vụ cơ bản", 1, "K3"),
        ("Khoa Quản lý nhà nước về an ninh, trật tự", 1, "K4"),
        ("Khoa Phản gián", 1, "K5"),
        ("Khoa An ninh xã hội", 1, "K6"),
        ("Khoa An ninh điều tra", 1, "K7"),
        ("Khoa An ninh chính trị nội bộ", 1, "K8"),
        ("Khoa An ninh kinh tế", 1, "K9"),
        ("Khoa Ngoại ngữ - Tin học", 1, "K10"),
        ("Khoa LLCT & KHXHNV", 1, "K11"),
        ("Khoa Quân sự, võ thuật, thể dục thể thao", 1, "K12"),
        # 5 Phòng (administrative)
        ("Phòng Hành chính tổng hợp", 0, "P1"),
        ("Phòng Chính trị", 0, "P2"),
        ("Phòng Quản lý đào tạo và bồi dưỡng nâng cao", 0, "P3"),
        ("Phòng Khảo thí và Đảm bảo chất lượng đào tạo", 0, "P4"),
        ("Phòng Quản lý nghiên cứu khoa học", 0, "P5"),
        # Dummy-coded units
        ("Phòng Hậu cần", 0, "P6"),
        ("Phòng Tổ chức cán bộ", 0, "P7"),
        ("Trung tâm Ngoại ngữ - Tin học", 0, "T1"),
        ("Trung tâm Thông tin Khoa học và Thư viện", 0, "T2"),
        ("Trung tâm Ứng dụng Công nghệ thông tin", 0, "T3"),
        ("Đoàn Thanh niên Cộng sản Hồ Chí Minh", 0, "Q1"),
        ("Hội Phụ nữ", 0, "Q2"),
        ("Công đoàn", 0, "Q3"),
        ("Hội Cựu chiến binh", 0, "Q4"),
    ]
    all_departments = legacy_departments + official_departments
    for name, is_teaching, code in all_departments:
        try:
            cursor.execute(
                "INSERT INTO departments (name, is_teaching_dept, dept_code) VALUES (?, ?, ?)",
                (name, is_teaching, code),
            )
        except Exception:
            try:
                cursor.execute(
                    "UPDATE departments SET dept_code = ? WHERE name = ?", (code, name)
                )
            except Exception:
                pass

    # Seed default admin user
    try:
        import bcrypt

        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO admin_users (username, password, role) VALUES ('admin', ?, 'admin')",
            (hashed,),
        )
    except Exception:
        pass

    seed_police_ranks(conn, cursor)

    # Reductions and Activities are seeded via separate scripts (seed_reductions.py, seed_activities.py)
    pass

    conn.commit()
    conn.close()


def seed_police_ranks(conn, cursor):
    ranks = [
        # Sĩ quan cấp tướng (Bảng 6, NĐ 204/2004/NĐ-CP)
        ("Đại tướng", 10.40, "SI_QUAN", 1),
        ("Thượng tướng", 9.80, "SI_QUAN", 2),
        ("Trung tướng", 9.20, "SI_QUAN", 3),
        ("Thiếu tướng", 8.60, "SI_QUAN", 4),
        # Sĩ quan cấp tá
        ("Đại tá", 8.00, "SI_QUAN", 5),
        ("Thượng tá", 7.30, "SI_QUAN", 6),
        ("Trung tá", 6.60, "SI_QUAN", 7),
        ("Thiếu tá", 6.00, "SI_QUAN", 8),
        # Sĩ quan cấp úy
        ("Đại úy", 5.40, "SI_QUAN", 9),
        ("Thượng úy", 5.00, "SI_QUAN", 10),
        ("Trung úy", 4.60, "SI_QUAN", 11),
        ("Thiếu úy", 4.20, "SI_QUAN", 12),
        # Hạ sĩ quan
        ("Thượng sĩ", 3.80, "HA_SI_QUAN", 13),
        ("Trung sĩ", 3.50, "HA_SI_QUAN", 14),
        ("Hạ sĩ", 3.20, "HA_SI_QUAN", 15),
        # Chuyên môn kỹ thuật — Nhóm 1 (ĐH)
        ("CMKT Nhóm 1 (Bậc 1)", 3.50, "CMKT_NHOM1", 16),
        ("CMKT Nhóm 1 (Bậc 2)", 4.05, "CMKT_NHOM1", 17),
        ("CMKT Nhóm 1 (Bậc 3)", 4.60, "CMKT_NHOM1", 18),
        ("CMKT Nhóm 1 (Bậc 4)", 5.15, "CMKT_NHOM1", 19),
        ("CMKT Nhóm 1 (Bậc 5)", 5.70, "CMKT_NHOM1", 20),
        ("CMKT Nhóm 1 (Bậc 6)", 6.25, "CMKT_NHOM1", 21),
        ("CMKT Nhóm 1 (Bậc 7)", 6.65, "CMKT_NHOM1", 22),
        # Chuyên môn kỹ thuật — Nhóm 2 (CĐ)
        ("CMKT Nhóm 2 (Bậc 1)", 3.20, "CMKT_NHOM2", 23),
        ("CMKT Nhóm 2 (Bậc 2)", 3.75, "CMKT_NHOM2", 24),
        ("CMKT Nhóm 2 (Bậc 3)", 4.30, "CMKT_NHOM2", 25),
        ("CMKT Nhóm 2 (Bậc 4)", 4.85, "CMKT_NHOM2", 26),
        ("CMKT Nhóm 2 (Bậc 5)", 5.40, "CMKT_NHOM2", 27),
        ("CMKT Nhóm 2 (Bậc 6)", 5.95, "CMKT_NHOM2", 28),
        ("CMKT Nhóm 2 (Bậc 7)", 6.35, "CMKT_NHOM2", 29),
    ]
    for rank_name, coefficient, rank_group, sort_order in ranks:
        try:
            cursor.execute(
                """
                INSERT INTO police_ranks (rank_name, coefficient, rank_group, sort_order)
                VALUES (?, ?, ?, ?)
            """,
                (rank_name, coefficient, rank_group, sort_order),
            )
        except Exception:
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


@st.cache_data(ttl=300)
def get_setting_value(key, default_value=None):
    """Lấy giá trị cấu hình từ bảng settings theo key, trả về default_value nếu không tồn tại."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return row[0]
    except Exception as e:
        print(f"Error reading setting {key}: {e}")
    finally:
        conn.close()
    return default_value


def get_base_salary(cursor=None):
    """Get base salary from settings, default 2,340,000 VND."""
    close_on_exit = False
    if cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        close_on_exit = True
    cursor.execute("SELECT value FROM settings WHERE key = 'base_salary'")
    row = cursor.fetchone()
    result = float(row["value"]) if row else 2340000.0
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


@st.cache_data(ttl=300)
def _cached_police_ranks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, rank_name, coefficient, rank_group FROM police_ranks ORDER BY sort_order"
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_police_ranks(cursor=None):
    """Return all police ranks sorted by rank_group, sort_order."""
    if cursor is None:
        return _cached_police_ranks()
    cursor.execute(
        "SELECT id, rank_name, coefficient, rank_group FROM police_ranks ORDER BY sort_order"
    )
    rows = cursor.fetchall()
    return [dict(r) for r in rows]


def get_teacher_rank_history(teacher_id, cursor=None):
    """Get rank history for a teacher, ordered by start_date."""
    close_on_exit = False
    if cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        close_on_exit = True
    cursor.execute(
        """
        SELECT rh.id, rh.teacher_id, rh.police_rank_id, rh.salary_coefficient,
               rh.start_date, rh.end_date, rh.note, pr.rank_name
        FROM teacher_rank_history rh
        JOIN police_ranks pr ON rh.police_rank_id = pr.id
        WHERE rh.teacher_id = ?
        ORDER BY rh.start_date ASC
    """,
        (teacher_id,),
    )
    rows = cursor.fetchall()
    if close_on_exit:
        conn.close()
    return [dict(r) for r in rows]


def compute_pro_rata_salary(teacher_id, timeframe_id):
    """Compute total_12m_salary with pro-rata for rank changes during a timeframe.
    Returns (total_12m, details) where details is a list of segment descriptions."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT start_date, end_date FROM timeframes WHERE id = ?", (timeframe_id,)
    )
    tf = cur.fetchone()
    if not tf:
        conn.close()
        return None, ["Timeframe not found"]
    tf_start, tf_end = tf["start_date"], tf["end_date"]
    cur.execute(
        "SELECT start_date, end_date FROM academic_holidays WHERE timeframe_id = ?",
        (timeframe_id,),
    )
    holidays = {r["start_date"]: r["end_date"] for r in cur.fetchall()}
    cur.execute("SELECT salary_coefficient FROM teachers WHERE id = ?", (teacher_id,))
    teacher = cur.fetchone()
    if not teacher:
        conn.close()
        return None, ["Teacher not found"]
    current_coeff = teacher["salary_coefficient"]
    if not current_coeff:
        conn.close()
        return None, ["No salary coefficient set"]
    rank_changes = get_teacher_rank_history(teacher_id, cur)
    changes_in_tf = [
        r
        for r in rank_changes
        if r["start_date"] <= tf_end
        and (r["end_date"] is None or r["end_date"] >= tf_start)
    ]
    base_salary = get_base_salary(cur)
    rank_annual = current_coeff * base_salary * 12
    if not changes_in_tf:
        conn.close()
        return rank_annual, [
            f"Hệ số {current_coeff} x {base_salary} x 12 = {rank_annual:,.0f} đ"
        ]
    total_days = _count_working_days(tf_start, tf_end, holidays)
    if total_days <= 0:
        conn.close()
        return rank_annual, [
            f"Cảnh báo: timeframe 0 ngày, dùng lương hiện tại {rank_annual:,.0f} đ"
        ]
    segments = []
    seg_starts = sorted(
        set(
            [tf_start]
            + [
                r["start_date"]
                for r in changes_in_tf
                if tf_start <= r["start_date"] <= tf_end
            ]
            + [
                r["end_date"]
                for r in changes_in_tf
                if r["end_date"] and tf_start <= r["end_date"] <= tf_end
            ]
        )
    )
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
            if r["start_date"] <= seg_start and (
                r["end_date"] is None or seg_start < r["end_date"]
            ):
                if matching is None or r["start_date"] > matching["start_date"]:
                    matching = r
        coeff = matching["salary_coefficient"] if matching else current_coeff
        seg_days = _count_working_days(seg_start, seg_end, holidays)
        if seg_days <= 0:
            continue
        seg_annual = coeff * base_salary * 12 * (seg_days / total_days)
        pro_rata_total += seg_annual
        details.append(
            f"{seg_start} đến {seg_end}: HS {coeff} × {seg_days}/{total_days} ngày = {seg_annual:,.0f} đ"
        )
    conn.close()
    if pro_rata_total <= 0:
        return rank_annual, [
            f"Không có ngày làm việc, dùng lương hiện tại {rank_annual:,.0f} đ"
        ]
    return pro_rata_total, details


def _count_working_days(start_date, end_date, holidays):
    """Count weekdays (Mon-Fri) between two dates inclusive, excluding holidays."""
    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    count = 0
    d = start
    while d <= end:
        if d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    for h_start, h_end in holidays.items():
        hs = datetime.strptime(h_start, "%Y-%m-%d").date()
        he = datetime.strptime(h_end, "%Y-%m-%d").date()
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
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM session_teacher_totals WHERE teacher_id = ?", (teacher_id,)
            )
            cursor.execute("DELETE FROM activity_logs WHERE teacher_id = ?", (teacher_id,))
            cursor.execute(
                "DELETE FROM teacher_role_history WHERE teacher_id = ?", (teacher_id,)
            )
            cursor.execute(
                "DELETE FROM teacher_rank_history WHERE teacher_id = ?", (teacher_id,)
            )
            cursor.execute("DELETE FROM manual_conversions WHERE teacher_id = ?", (teacher_id,))
            cursor.execute("DELETE FROM payroll_records WHERE teacher_id = ?", (teacher_id,))
            cursor.execute("DELETE FROM bulk_teaching_assignments WHERE teacher_id = ?", (teacher_id,))
            cursor.execute("DELETE FROM teacher_calculated_totals WHERE teacher_id = ?", (teacher_id,))
            cursor.execute("UPDATE admin_users SET teacher_id = NULL WHERE teacher_id = ?", (teacher_id,))
            cursor.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
    finally:
        conn.close()


def delete_timeframe(timeframe_id, conn=None):
    if conn is None:
        conn = get_connection()
        should_close = True
    else:
        should_close = False

    try:
        if should_close:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM academic_holidays WHERE timeframe_id = ?", (timeframe_id,)
                )
                cursor.execute("DELETE FROM activity_logs WHERE timeframe_id = ?", (timeframe_id,))
                cursor.execute(
                    "DELETE FROM payroll_records WHERE timeframe_id = ?", (timeframe_id,)
                )
                cursor.execute(
                    "DELETE FROM manual_conversions WHERE timeframe_id = ?", (timeframe_id,)
                )
                cursor.execute(
                    "DELETE FROM session_teacher_totals WHERE timeframe_id = ?", (timeframe_id,)
                )
                cursor.execute(
                    "DELETE FROM bulk_teaching_assignments WHERE timeframe_id = ?", (timeframe_id,)
                )
                cursor.execute(
                    "DELETE FROM bulk_import_files WHERE timeframe_id = ?", (timeframe_id,)
                )
                cursor.execute(
                    "DELETE FROM teacher_calculated_totals WHERE timeframe_id = ?", (timeframe_id,)
                )
                cursor.execute("DELETE FROM timeframes WHERE id = ?", (timeframe_id,))
        else:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM academic_holidays WHERE timeframe_id = ?", (timeframe_id,)
            )
            cursor.execute("DELETE FROM activity_logs WHERE timeframe_id = ?", (timeframe_id,))
            cursor.execute(
                "DELETE FROM payroll_records WHERE timeframe_id = ?", (timeframe_id,)
            )
            cursor.execute(
                "DELETE FROM manual_conversions WHERE timeframe_id = ?", (timeframe_id,)
            )
            cursor.execute(
                "DELETE FROM session_teacher_totals WHERE timeframe_id = ?", (timeframe_id,)
            )
            cursor.execute(
                "DELETE FROM bulk_teaching_assignments WHERE timeframe_id = ?", (timeframe_id,)
            )
            cursor.execute(
                "DELETE FROM bulk_import_files WHERE timeframe_id = ?", (timeframe_id,)
            )
            cursor.execute(
                "DELETE FROM teacher_calculated_totals WHERE timeframe_id = ?", (timeframe_id,)
            )
            cursor.execute("DELETE FROM timeframes WHERE id = ?", (timeframe_id,))
    finally:
        if should_close:
            conn.close()

    try:
        get_cached_timeframes.clear()
    except Exception:
        pass


@st.cache_data(ttl=300)
def get_cached_timeframes():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, name, start_date, end_date FROM timeframes ORDER BY start_date DESC",
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_cached_teachers():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, name, subject_group, employment_type FROM teachers ORDER BY name",
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=300)
def get_cached_activity_types():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM activity_types", conn)
    conn.close()
    return df


HOLIDAY_PRESETS = {
    "2024-2025": {
        "tet_start": "2025-01-27",
        "tet_end": "2025-02-16",
        "hung_vuong": "2025-04-07",
    },
    "2025-2026": {
        "tet_start": "2026-01-26",
        "tet_end": "2026-02-15",
        "hung_vuong": "2026-04-26",
    },
    "2026-2027": {
        "tet_start": "2027-02-15",
        "tet_end": "2027-03-07",
        "hung_vuong": "2027-04-16",
    },
}


def seed_holidays_for_timeframe(conn, timeframe_id, name, start_date_str, end_date_str):
    cursor = conn.cursor()

    preset_key = "2025-2026"  # fallback default
    for k in HOLIDAY_PRESETS.keys():
        if k in name:
            preset_key = k
            break

    preset = HOLIDAY_PRESETS[preset_key]

    from datetime import datetime

    try:
        dt_start = datetime.strptime(start_date_str, "%Y-%m-%d")
        dt_end = datetime.strptime(end_date_str, "%Y-%m-%d")
        y_start, y_end = dt_start.year, dt_end.year
    except Exception:
        parts = preset_key.split("-")
        y_start, y_end = int(parts[0]), int(parts[1])

    # Seed ONLY non-summer holidays. Summer break is represented by the gap.
    holidays = [
        ("Nghỉ Tết Nguyên đán", preset["tet_start"], preset["tet_end"]),
        ("Nghỉ Giỗ tổ Hùng Vương", preset["hung_vuong"], preset["hung_vuong"]),
        ("Ngày Truyền thống CAND (19/8)", f"{y_start}-08-19", f"{y_start}-08-19"),
        ("Nghỉ Lễ Quốc khánh (2/9)", f"{y_start}-09-02", f"{y_start}-09-03"),
        ("Nghỉ Tết Dương lịch", f"{y_end}-01-01", f"{y_end}-01-01"),
        ("Nghỉ Lễ 30/4 & 1/5", f"{y_end}-04-30", f"{y_end}-05-01"),
    ]

    cursor.execute(
        """
        DELETE FROM academic_holidays 
        WHERE timeframe_id = ? AND name IN (
            'Nghỉ Tết Nguyên đán', 'Nghỉ Hè', 'Ngày Truyền thống CAND (19/8)',
            'Nghỉ Lễ Quốc khánh (2/9)', 'Nghỉ Tết Dương lịch', 
            'Nghỉ Giỗ tổ Hùng Vương', 'Nghỉ Lễ 30/4 & 1/5'
        )
    """,
        (timeframe_id,),
    )

    for h_name, h_start, h_end in holidays:
        cursor.execute(
            "INSERT INTO academic_holidays (timeframe_id, name, start_date, end_date) VALUES (?, ?, ?, ?)",
            (timeframe_id, h_name, h_start, h_end),
        )


if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    seed_initial_data()
    print("DB created. Data seeded.")
