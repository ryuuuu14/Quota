import pytest
import os
import sqlite3
import bcrypt
from database import init_db, get_connection
from auth import authenticate_user, get_scoped_teacher_ids, require_role

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    test_db = os.path.join(tmp_path, "test_auth_portal.sqlite")
    os.environ["DB_PATH"] = test_db
    init_db()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Seed department codes & mock departments
    departments = [
        ('Chính trị, Pháp luật, Nghiệp vụ', '3333'),
        ('Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học', '1111')
    ]
    for dept_name, code in departments:
        cursor.execute("INSERT OR IGNORE INTO departments (name, is_teaching_dept, dept_code) VALUES (?, 1, ?)", (dept_name, code))
        
    # Seed mock teachers
    teachers = [
        ('Teacher A', 'Chính trị, Pháp luật, Nghiệp vụ'),
        ('Teacher B', 'Chính trị, Pháp luật, Nghiệp vụ'),
        ('Teacher C', 'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học')
    ]
    for name, dept in teachers:
        cursor.execute("INSERT INTO teachers (name, subject_group, employment_type) VALUES (?, 'Tổ bộ môn', 'TEACHER')", (name,))
        teacher_id = cursor.lastrowid
        cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (?, 'DEPARTMENT', ?, '2026-01-01')", (teacher_id, dept))

    conn.commit()
    conn.close()
    yield
    if "DB_PATH" in os.environ:
        del os.environ["DB_PATH"]

def test_authenticate_user_plaintext_migration():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Insert a user with plaintext password
    cursor.execute("""
        INSERT INTO admin_users (username, password, role, department_name)
        VALUES (?, ?, ?, ?)
    """, ("legacy_user", "legacy123", "head_dept", "Chính trị, Pháp luật, Nghiệp vụ"))
    conn.commit()
    
    # 2. Verify it is plaintext initially
    cursor.execute("SELECT password FROM admin_users WHERE username = ?", ("legacy_user",))
    pwd = cursor.fetchone()[0]
    assert pwd == "legacy123"
    
    # 3. Authenticate to trigger plaintext-to-bcrypt upgrade
    user = authenticate_user("legacy_user", "legacy123")
    assert user is not None
    assert user["username"] == "legacy_user"
    assert user["role"] == "head_dept"
    assert user["department_name"] == "Chính trị, Pháp luật, Nghiệp vụ"
    
    # 4. Verify password in DB is now hashed with bcrypt
    cursor.execute("SELECT password FROM admin_users WHERE username = ?", ("legacy_user",))
    pwd_hashed = cursor.fetchone()[0]
    assert pwd_hashed.startswith("$2b$") or pwd_hashed.startswith("$2a$")
    
    # 5. Verify subsequent authentication works with same password
    user_hashed = authenticate_user("legacy_user", "legacy123")
    assert user_hashed is not None
    assert user_hashed["username"] == "legacy_user"
    
    # 6. Verify authentication fails with wrong password
    assert authenticate_user("legacy_user", "wrong123") is None
    
    conn.close()

def test_get_scoped_teacher_ids():
    conn = get_connection()
    
    # Fetch actual teacher IDs from database
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'DEPARTMENT' ORDER BY start_date DESC LIMIT 1) as dept
        FROM teachers t
    """)
    rows = cursor.fetchall()
    
    dept_1_teachers = [r[0] for r in rows if r[1] == 'Chính trị, Pháp luật, Nghiệp vụ']
    dept_2_teachers = [r[0] for r in rows if r[1] == 'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học']
    
    # 1. Admin user has no scoped_ids restriction (returns None)
    admin_user = {"username": "admin", "role": "admin", "department_name": None}
    assert get_scoped_teacher_ids(admin_user) is None
    
    # 2. Head of department "Chính trị, Pháp luật, Nghiệp vụ" has scoped_ids restricted to their department
    head_user_1 = {"username": "head1", "role": "head_dept", "department_name": "Chính trị, Pháp luật, Nghiệp vụ"}
    scoped_ids_1 = get_scoped_teacher_ids(head_user_1)
    assert scoped_ids_1 is not None
    assert set(scoped_ids_1) == set(dept_1_teachers)
    
    # 3. Head of department "Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học" has scoped_ids restricted to theirs
    head_user_2 = {"username": "head2", "role": "head_dept", "department_name": "Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học"}
    scoped_ids_2 = get_scoped_teacher_ids(head_user_2)
    assert scoped_ids_2 is not None
    assert set(scoped_ids_2) == set(dept_2_teachers)
    
    # 4. Anonymous user or None user returns None
    assert get_scoped_teacher_ids(None) is None
    
    conn.close()
