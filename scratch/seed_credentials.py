import os
import sys
import sqlite3
import bcrypt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from database import get_connection, init_db

# 1. Initialize database and ensure tables exist
init_db()

conn = get_connection()
cursor = conn.cursor()

def hash_pw(pw):
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Clear old credentials from admin_users
try:
    cursor.execute("DELETE FROM admin_users")
    print("Cleared existing users from admin_users table.")
except Exception as e:
    print(f"Error clearing admin_users: {e}")

# 2. Define and seed admin user
admin_username = 'admin'
admin_password = 'admin123'
try:
    hashed_admin_pw = hash_pw(admin_password)
    cursor.execute("""
        INSERT INTO admin_users (username, password, role, department_name)
        VALUES (?, ?, 'admin', NULL)
    """, (admin_username, hashed_admin_pw))
    print("Seeded admin user successfully.")
except Exception as e:
    print(f"Error seeding admin user: {e}")

# 3. Retrieve all departments that have a valid department code
try:
    cursor.execute("SELECT name, dept_code FROM departments WHERE dept_code IS NOT NULL AND dept_code != ''")
    depts = cursor.fetchall()
except Exception as e:
    print(f"Error reading departments: {e}")
    depts = []

# 4. Seed head_dept users
seeded_head_depts = []
for row in depts:
    dept_name = row['name']
    dept_code = str(row['dept_code']).strip()
    
    # Username is the department code, password is '123'
    username = dept_code
    password = '123'
    role = 'head_dept'
    
    try:
        hashed_pw = hash_pw(password)
        cursor.execute("""
            INSERT INTO admin_users (username, password, role, department_name)
            VALUES (?, ?, ?, ?)
        """, (username, hashed_pw, role, dept_name))
        seeded_head_depts.append((username, password, role, dept_name))
    except Exception as e:
        print(f"Error seeding head_dept user for {dept_name} ({dept_code}): {e}")

conn.commit()
conn.close()

# 5. Write summary to credentials.txt in UTF-8
summary_path = os.path.join(os.path.dirname(__file__), 'credentials.txt')
try:
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=== HỆ THỐNG QUẢN LÝ T04 - THÔNG TIN ĐĂNG NHẬP / XÁC THỰC ===\n\n")
        f.write("1. TÀI KHOẢN NGƯỜI DÙNG (USERS):\n")
        f.write(f"   - Tên đăng nhập: {admin_username}\n")
        f.write(f"     Mật khẩu:     {admin_password}\n")
        f.write(f"     Vai trò:      admin\n\n")
        
        for username, password, role, dept_name in seeded_head_depts:
            f.write(f"   - Tên đăng nhập: {username}\n")
            f.write(f"     Mật khẩu:     {password}\n")
            f.write(f"     Vai trò:      {role}\n")
            f.write(f"     Đơn vị:       {dept_name}\n\n")
            
    print("Seeding completed successfully! Details saved to scratch/credentials.txt")
except Exception as e:
    print(f"Error writing credentials file: {e}")
