import os
from database import get_connection, init_db, seed_initial_data


def test_db_schema_and_seeding(tmp_path):
    # Setup isolated test database
    test_db = os.path.join(tmp_path, "test_staging.sqlite")
    os.environ["DB_PATH"] = test_db

    # Initialize and seed
    init_db()
    seed_initial_data()

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Verify admin_users table exists and is seeded
    cursor.execute("SELECT username, password FROM admin_users")
    admins = cursor.fetchall()
    import bcrypt

    assert len(admins) == 1
    assert admins[0]["username"] == "admin"
    assert (
        bcrypt.checkpw(b"admin123", admins[0]["password"].encode("utf-8"))
        or admins[0]["password"] == "admin123"
    )

    # 2. Verify departments have codes
    cursor.execute("SELECT name, dept_code FROM departments")
    depts = {row["name"]: row["dept_code"] for row in cursor.fetchall()}
    assert depts["Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học"] == "1111"
    assert depts["Nhà giáo giảng dạy thực hành"] == "2222"
    assert depts["Chính trị, Pháp luật, Nghiệp vụ"] == "3333"
    assert depts["Công tác tại phòng, trung tâm"] == "4444"

    # 3. Verify staging tables exist
    tables = [
        "staging_teachers",
        "staging_activities",
        "staging_schedule",
        "import_batches",
    ]
    for t in tables:
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t}'"
        )
        assert cursor.fetchone() is not None

    conn.close()
