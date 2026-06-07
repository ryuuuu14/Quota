import sqlite3
import os
from database import get_connection, init_db, seed_initial_data

def run():
    print("Khởi chạy seed dữ liệu tạm thời (staging mock records)...")
    init_db()
    seed_initial_data()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Seed Staging Teachers Batch
    try:
        cursor.execute("""
            INSERT INTO import_batches (domain, dept_name, uploaded_by, filename, row_count, status)
            VALUES ('teachers', 'Khoa CNTT', 'giangvien_cntt', 'danh_sach_bo_sung.xlsx', 2, 'pending')
        """)
        batch_teachers_id = cursor.lastrowid
        
        # Add new teacher
        cursor.execute("""
            INSERT INTO staging_teachers (
                batch_id, row_num, teacher_name, department, title, employment_type,
                guest_rank, total_12m_salary, police_rank_id, salary_coefficient, is_female, subject_group, diff_marker, diff_detail
            ) VALUES (?, 5, 'Trần Minh Tuấn', 'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học', 'Giảng viên', 'TEACHER', NULL, 18000000.0, NULL, 3.5, 0, 'Tự nhiên/Kỹ thuật', 'NEW', 'Cán bộ mới tuyển dụng')
        """, (batch_teachers_id,))
        
        # Add update teacher
        cursor.execute("""
            INSERT INTO staging_teachers (
                batch_id, row_num, teacher_name, department, title, employment_type,
                guest_rank, total_12m_salary, police_rank_id, salary_coefficient, is_female, subject_group, diff_marker, diff_detail
            ) VALUES (?, 6, 'Nguyễn Văn A', 'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học', 'Giảng viên chính', 'TEACHER', NULL, 22000000.0, NULL, 5.7, 0, 'Tự nhiên/Kỹ thuật', 'UPDATE', 'Chức danh: Giảng viên -> Giảng viên chính, Hệ số lương: 4.4 -> 5.7')
        """, (batch_teachers_id,))
        
        print(f"✓ Đã seed lô cán bộ tạm thời (Batch ID: {batch_teachers_id})")
    except Exception as e:
        print(f"Lỗi khi seed cán bộ tạm thời: {e}")
        
    # 2. Seed Staging Activities Batch
    try:
        cursor.execute("""
            INSERT INTO import_batches (domain, dept_name, uploaded_by, filename, row_count, status)
            VALUES ('activities', 'Khoa Chính trị', 'giangvien_chinhtri', 'hoat_dong_nckh.xlsx', 1, 'pending')
        """)
        batch_act_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO staging_activities (
                batch_id, row_num, diff_marker, diff_detail, validation_errors,
                teacher_name, activity_type_name, log_date, quantity,
                class_level, class_type, student_count, nckh_level,
                is_main_author, is_foreign_language_instruction, note, timeframe_name
            ) VALUES (
                ?, 10, 'NEW', 'Hoạt động mới bổ sung', '',
                'Nguyễn Văn A', 'Hướng dẫn luận văn thạc sĩ', '2026-03-15', 1.0,
                'CAO_HOC', 'Lý thuyết', 1, NULL,
                1, 0, 'Hướng dẫn học viên Nguyễn Văn B bảo vệ thành công', 'Năm học 2025-2026'
            )
        """, (batch_act_id,))
        
        print(f"✓ Đã seed lô hoạt động tạm thời (Batch ID: {batch_act_id})")
    except Exception as e:
        print(f"Lỗi khi seed hoạt động tạm thời: {e}")
        
    conn.commit()
    conn.close()
    print("Hoàn tất seed dữ liệu tạm thời!")

if __name__ == "__main__":
    run()
