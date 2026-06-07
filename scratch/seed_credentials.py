import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from database import get_connection, init_db

# 1. Initialize database and ensure tables exist
init_db()

conn = get_connection()
cursor = conn.cursor()

import bcrypt

def hash_pw(pw):
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 2. Add extra user credentials
users = [
    ('admin', 'admin123', 'admin', None),
    ('manager_t04', 'manager123', 'admin', None),
    ('approver_t04', 'approver123', 'admin', None),
    ('head_tunhien', 'head123', 'head_dept', 'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học'),
    ('head_thuchanh', 'head123', 'head_dept', 'Nhà giáo giảng dạy thực hành'),
    ('head_chinhtri', 'head123', 'head_dept', 'Chính trị, Pháp luật, Nghiệp vụ'),
    ('head_phong', 'head123', 'head_dept', 'Công tác tại phòng, trung tâm'),
]

for username, password, role, dept in users:
    try:
        hashed_pw = hash_pw(password)
        cursor.execute("""
            INSERT INTO admin_users (username, password, role, department_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password = excluded.password,
                role = excluded.role,
                department_name = excluded.department_name
        """, (username, hashed_pw, role, dept))
    except Exception as e:
        print(f"Error seeding user {username}: {e}")

# 3. Add/Update department codes
departments_data = [
    ('Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học', '1111'),
    ('Nhà giáo giảng dạy thực hành', '2222'),
    ('Chính trị, Pháp luật, Nghiệp vụ', '3333'),
    ('Công tác tại phòng, trung tâm', '4444')
]

for name, code in departments_data:
    try:
        # Check if department exists
        cursor.execute("SELECT name FROM departments WHERE name = ?", (name,))
        if cursor.fetchone():
            cursor.execute("UPDATE departments SET dept_code = ? WHERE name = ?", (code, name))
        else:
            cursor.execute("INSERT INTO departments (name, is_teaching_dept, dept_code) VALUES (?, 1, ?)", (name, code))
    except Exception as e:
        print(f"Error seeding department {name}: {e}")

conn.commit()
conn.close()

# 4. Write summary to file in UTF-8
summary_path = os.path.join(os.path.dirname(__file__), 'credentials.txt')
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write("=== HỆ THỐNG QUẢN LÝ T04 - THÔNG TIN ĐĂNG NHẬP / XÁC THỰC ===\n\n")
    f.write("1. TÀI KHOẢN NGƯỜI DÙNG (USERS):\n")
    for username, password, role, dept in users:
        f.write(f"   - Tên đăng nhập: {username}\n")
        f.write(f"     Mật khẩu:     {password}\n")
        f.write(f"     Vai trò:      {role}\n")
        if dept:
            f.write(f"     Đơn vị:       {dept}\n")
        f.write("\n")
    
    f.write("2. MÃ XÁC THỰC KHOA / BỘ MÔN (DEPARTMENT SECURITY CODES):\n")
    for name, code in departments_data:
        f.write(f"   - Đơn vị: {name}\n")
        f.write(f"     Mã xác thực: {code}\n\n")

print("Seeding completed successfully! Details saved to scratch/credentials.txt")
