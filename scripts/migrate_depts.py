"""
migrate_depts.py — Import official departments with correct K/P codes.
Usage:
    python scripts/migrate_depts.py              # dry-run
    python scripts/migrate_depts.py --apply       # apply changes
"""
import sqlite3, sys, os

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)
DB_PATH = os.path.join(_project_root, 'data', 'database.sqlite')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Correct official departments
OFFICIAL_DEPARTMENTS = [
    ('Ban Giám hiệu',                                          0, 'BGH'),
    # 12 Khoa (teaching)
    ('Khoa Lý luận chính trị và Khoa học xã hội nhân văn',     1, 'K1'),
    ('Khoa Luật',                                               1, 'K2'),
    ('Khoa Nghiệp vụ cơ bản',                                  1, 'K3'),
    ('Khoa Quản lý nhà nước về an ninh, trật tự',              1, 'K4'),
    ('Khoa Phản gián',                                          1, 'K5'),
    ('Khoa An ninh xã hội',                                     1, 'K6'),
    ('Khoa An ninh điều tra',                                   1, 'K7'),
    ('Khoa An ninh chính trị nội bộ',                           1, 'K8'),
    ('Khoa An ninh kinh tế',                                    1, 'K9'),
    ('Khoa Ngoại ngữ - Tin học',                                1, 'K10'),
    ('Khoa LLCT & KHXHNV',                                      1, 'K11'),
    ('Khoa Quân sự, võ thuật, thể dục thể thao',               1, 'K12'),
    # 5 Phòng (administrative)
    ('Phòng Hành chính tổng hợp',                               0, 'P1'),
    ('Phòng Chính trị',                                         0, 'P2'),
    ('Phòng Quản lý đào tạo và bồi dưỡng nâng cao',           0, 'P3'),
    ('Phòng Khảo thí và Đảm bảo chất lượng đào tạo',          0, 'P4'),
    ('Phòng Quản lý nghiên cứu khoa học',                      0, 'P5'),
    # Dummy units (from original org chart, codes assigned)
    ('Phòng Hậu cần',                                          0, 'P6'),
    ('Phòng Tổ chức cán bộ',                                   0, 'P7'),
    ('Trung tâm Ngoại ngữ - Tin học',                          0, 'T1'),
    ('Trung tâm Thông tin Khoa học và Thư viện',               0, 'T2'),
    ('Trung tâm Ứng dụng Công nghệ thông tin',                0, 'T3'),
    ('Đoàn Thanh niên Cộng sản Hồ Chí Minh',                  0, 'Q1'),
    ('Hội Phụ nữ',                                             0, 'Q2'),
    ('Công đoàn',                                               0, 'Q3'),
    ('Hội Cựu chiến binh',                                     0, 'Q4'),
]

OFFICIAL_NAMES = {name for name, _, _ in OFFICIAL_DEPARTMENTS}

# Wrong departments from previous migration that must be deleted
WRONG_DEPTS = [
    'Khoa An ninh quốc gia',
    'Khoa An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao',
    'Khoa Trinh sát an ninh',
    'Khoa Quản lý nhà nước về an ninh trật tự',  # old wrong name (missing comma)
    'Khoa Ngoại ngữ',
    'Khoa Cơ sở cơ bản',
    'Khoa Quân sự, võ thuật và thể dục thể thao',  # old wrong name ("và" instead of comma)
    'Khoa Nghiệp vụ an ninh',
    'Khoa Cảnh sát',
    'Khoa Khoa học dữ liệu',
    'Phòng Khảo thí và đảm bảo chất lượng đào tạo',  # old wrong casing
    'Phòng Kế hoạch - Tài chính',
]

# Fix references that point to wrong department names
FIXUP_MAP = {
    'Khoa An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao': 'Khoa Ngoại ngữ - Tin học',
    'Khoa Cơ sở cơ bản':                                                 'Khoa Ngoại ngữ - Tin học',
    'Khoa Quân sự, võ thuật và thể dục thể thao':                        'Khoa Quân sự, võ thuật, thể dục thể thao',
    'Khoa Quản lý nhà nước về an ninh trật tự':                          'Khoa Quản lý nhà nước về an ninh, trật tự',
    'Phòng Khảo thí và đảm bảo chất lượng đào tạo':                     'Phòng Khảo thí và Đảm bảo chất lượng đào tạo',
    # Legacy generic → closest official
    'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học':   'Khoa Ngoại ngữ - Tin học',
    'Nhà giáo giảng dạy thực hành':              'Khoa Quân sự, võ thuật, thể dục thể thao',
    'Chính trị, Pháp luật, Nghiệp vụ':           'Khoa Lý luận chính trị và Khoa học xã hội nhân văn',
    'Công tác tại phòng, trung tâm':              'Phòng Hành chính tổng hợp',
    'Khoa Xã hội':                                'Khoa Lý luận chính trị và Khoa học xã hội nhân văn',
    'Khoa Kỹ thuật':                              'Khoa Ngoại ngữ - Tin học',
    'Khoa CNTT':                                  'Khoa Ngoại ngữ - Tin học',
    'Khoa Chính trị':                             'Khoa Lý luận chính trị và Khoa học xã hội nhân văn',
}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def migrate(dry_run=True):
    conn = get_connection()
    cur = conn.cursor()
    print(f"{'[DRY-RUN]' if dry_run else '[APPLYING]'} Migration: Correct Department Codes")
    print(f"Database: {DB_PATH}\n")

    # Phase 1: Insert correct departments FIRST (so FK targets exist)
    print("--- Phase 1: Insert correct departments ---")
    inserted, skipped = 0, 0
    for name, is_teaching, code in OFFICIAL_DEPARTMENTS:
        cur.execute("SELECT name, dept_code FROM departments WHERE name = ?", (name,))
        existing = cur.fetchone()
        if existing:
            if existing['dept_code'] != code:
                print(f"  UPDATE code: {name} → {code}")
                if not dry_run:
                    cur.execute("UPDATE departments SET dept_code = ?, is_teaching_dept = ? WHERE name = ?",
                                (code, is_teaching, name))
            else:
                print(f"  SKIP: {code} — {name}")
            skipped += 1
        else:
            print(f"  INSERT: {code} — {name} (teaching={is_teaching})")
            if not dry_run:
                cur.execute("INSERT INTO departments (name, is_teaching_dept, dept_code) VALUES (?, ?, ?)",
                            (name, is_teaching, code))
            inserted += 1
    print(f"  → Inserted: {inserted}, Skipped/Updated: {skipped}")

    # Phase 2: Fix references (now that correct departments exist)
    print("\n--- Phase 2: Fix references ---")
    for table, col in [
        ('teacher_role_history', 'value_text'),
        ('admin_users', 'department_name'),
        ('import_batches', 'dept_name'),
    ]:
        cond_prefix = "record_type = 'DEPARTMENT' AND " if table == 'teacher_role_history' else ''
        cur.execute(f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL")
        refs = [r[0] for r in cur.fetchall()]
        for ref in refs:
            if ref in FIXUP_MAP:
                new = FIXUP_MAP[ref]
                cond = f"{cond_prefix}{col} = ?"
                cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {cond}", (ref,))
                cnt = cur.fetchone()[0]
                print(f"  [{table}] '{ref}' → '{new}' ({cnt})")
                if not dry_run:
                    cur.execute(f"UPDATE {table} SET {col} = ? WHERE {cond}", (new, ref))

    # Phase 3: Delete wrong departments (references already fixed)
    print("\n--- Phase 3: Delete wrong departments ---")
    for name in WRONG_DEPTS:
        cur.execute("SELECT name FROM departments WHERE name = ?", (name,))
        if cur.fetchone():
            cur.execute("SELECT COUNT(*) FROM admin_users WHERE department_name = ?", (name,))
            fk_count = cur.fetchone()[0]
            if fk_count > 0:
                print(f"  SKIP (still referenced by {fk_count} admin_users): {name}")
                continue
            print(f"  DELETE: {name}")
            if not dry_run:
                cur.execute("DELETE FROM departments WHERE name = ?", (name,))

    # Phase 4: Legacy departments kept
    print("\n--- Phase 4: Legacy departments preserved ---")
    for d in ['Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học', 'Nhà giáo giảng dạy thực hành',
              'Chính trị, Pháp luật, Nghiệp vụ', 'Công tác tại phòng, trung tâm']:
        print(f"  KEPT: {d}")

    if dry_run:
        print("\n=== DRY-RUN COMPLETE ===")
        conn.rollback()
    else:
        conn.commit()
        print("\n=== MIGRATION APPLIED ===")
    conn.close()


if __name__ == '__main__':
    migrate(dry_run='--apply' not in sys.argv)
