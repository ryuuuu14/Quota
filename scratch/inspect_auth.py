import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from database import get_connection, init_db

init_db()

conn = get_connection()
cursor = conn.cursor()

print("--- Admin Users ---")
try:
    cursor.execute("SELECT id, username, password FROM admin_users")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row['id']} | Username: {row['username']} | Password: {row['password']}")
except Exception as e:
    print(f"Error reading admin_users: {e}")

print("\n--- Departments & Codes ---")
try:
    cursor.execute("SELECT name, dept_code FROM departments")
    rows = cursor.fetchall()
    for row in rows:
        print(f"Name: {row['name']} | Code: {row['dept_code']}")
except Exception as e:
    print(f"Error reading departments: {e}")

conn.close()
