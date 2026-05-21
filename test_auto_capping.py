import sqlite3
import pytest
import os
import sys
from unittest import mock



DB_PATH = 'test_db.sqlite'

def setup_module(module):
    # Initialize a test DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY, name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS teacher_role_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER,
        record_type TEXT,
        value_text TEXT,
        start_date DATE,
        end_date DATE)''')

    cursor.execute("DELETE FROM teachers")
    cursor.execute("DELETE FROM teacher_role_history")
    cursor.execute("INSERT INTO teachers (id, name) VALUES (1, 'Test Teacher')")
    conn.commit()
    conn.close()

def teardown_module(module):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_auto_capping_logic():
    # Simulate UI logic
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Add first title
    start_date_1 = '2023-01-01'
    rec_type = 'TITLE'
    cursor.execute("""
        UPDATE teacher_role_history
        SET end_date = ?
        WHERE teacher_id = ? AND record_type = ? AND end_date IS NULL
    """, (start_date_1, 1, rec_type))

    cursor.execute("""
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, ?, ?, ?, ?)
    """, (1, rec_type, "Giảng viên", start_date_1, None))
    conn.commit()

    # Verify first title
    res = cursor.execute("SELECT * FROM teacher_role_history WHERE teacher_id=1").fetchall()
    assert len(res) == 1
    assert res[0][5] is None # end_date is None

    # 2. Add second title
    start_date_2 = '2024-01-01'
    cursor.execute("""
        UPDATE teacher_role_history
        SET end_date = ?
        WHERE teacher_id = ? AND record_type = ? AND end_date IS NULL
    """, (start_date_2, 1, rec_type))

    cursor.execute("""
        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date, end_date)
        VALUES (?, ?, ?, ?, ?)
    """, (1, rec_type, "Giảng viên chính", start_date_2, None))
    conn.commit()

    # Verify auto-capping
    res = cursor.execute("SELECT * FROM teacher_role_history WHERE teacher_id=1 ORDER BY start_date").fetchall()
    assert len(res) == 2
    assert res[0][3] == "Giảng viên"
    assert res[0][5] == "2024-01-01" # Auto capped

    assert res[1][3] == "Giảng viên chính"
    assert res[1][5] is None

    conn.close()
