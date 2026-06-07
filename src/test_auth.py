import pytest
import os
from database import init_db, seed_initial_data
from auth import verify_admin, verify_department_code, get_all_departments_with_codes

def test_auth_and_dept_verification(tmp_path):
    test_db = os.path.join(tmp_path, "test_auth.sqlite")
    os.environ["DB_PATH"] = test_db

    init_db()
    seed_initial_data()

    # 1. Test Admin login verification
    assert verify_admin("admin", "admin123") is True
    assert verify_admin("admin", "wrongpassword") is False
    assert verify_admin("nonexistent", "admin123") is False

    # 2. Test Department Code verification
    assert verify_department_code("Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học", "1111") is True
    assert verify_department_code("Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học", "1234") is False
    assert verify_department_code("Nonexistent Department", "1111") is False

    # 3. Test list depts
    depts = get_all_departments_with_codes()
    assert len(depts) >= 4
    names = [d["name"] for d in depts]
    assert "Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học" in names
