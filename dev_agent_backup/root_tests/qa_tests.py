import sys
import os

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


# Redirect sqlite3 connections to test_qa.sqlite to preserve the real DB
import sqlite3
original_connect = sqlite3.connect
def mock_connect(database, *args, **kwargs):
    return original_connect('test_qa.sqlite', *args, **kwargs)
sqlite3.connect = mock_connect

# Set DB_PATH environment variable for consistency
os.environ['DB_PATH'] = 'test_qa.sqlite'

# Clean up existing test database if any
if os.path.exists('test_qa.sqlite'):
    try:
        os.remove('test_qa.sqlite')
    except Exception:
        pass

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import init_db, seed_initial_data, get_connection
import seed_reductions
import seed_activities
import pandas as pd
from calculations import calculate_teacher_metrics

def setup_qa_data():
    # Initialize and seed initial data
    init_db()
    seed_initial_data()
    seed_reductions.run()
    seed_activities.run()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Insert QA timeframe (Năm học 2026)
    cursor.execute("""
        INSERT OR REPLACE INTO timeframes (id, name, start_date, end_date, norm_multiplier, standard_academic_weeks)
        VALUES (99, 'QA Timeframe 2026', '2026-01-01', '2026-12-31', 1.0, 44.0)
    """)
    
    # Clear out tables
    cursor.execute("DELETE FROM teacher_role_history")
    cursor.execute("DELETE FROM teachers")
    cursor.execute("DELETE FROM activity_logs")
    cursor.execute("DELETE FROM manual_conversions")
    
    # Look up reduction rule IDs
    cursor.execute("SELECT id FROM reduction_rules WHERE name = 'Trưởng khoa'")
    tk_rule_id = cursor.fetchone()[0]
    
    cursor.execute("SELECT id FROM reduction_rules WHERE name = 'Nữ nuôi con nhỏ từ 12 đến dưới 36 tháng'")
    child_rule_id = cursor.fetchone()[0]
    
    # Look up activity type IDs
    cursor.execute("SELECT id FROM activity_types WHERE name LIKE 'GD - Lý thuyết ĐH%'")
    teaching_act_id = cursor.fetchone()[0]
    
    cursor.execute("SELECT id FROM activity_types WHERE name = 'NCKH - Bài báo ISI/Scopus'")
    nckh_act_id = cursor.fetchone()[0]
    
    # Scenario 1: Giảng viên bình thường (Tự nhiên, 270 GC)
    cursor.execute("INSERT INTO teachers (id, name, subject_group, is_female) VALUES (1, 'GV Binh Thuong', 'Tự nhiên/Kỹ thuật', 0)")
    cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (1, 'TITLE', 'Giảng viên', '2026-01-01')")
    cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (1, 'DEPARTMENT', 'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học', '2026-01-01')")
    
    # Scenario 2: Trưởng khoa nữ có con nhỏ (Max reduction rule: 40% role reduction + 10% special child reduction)
    cursor.execute("INSERT INTO teachers (id, name, subject_group, is_female) VALUES (2, 'Truong Khoa Nu', 'Tự nhiên/Kỹ thuật', 1)")
    cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (2, 'TITLE', 'Giảng viên', '2026-01-01')")
    cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (2, 'DEPARTMENT', 'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học', '2026-01-01')")
    cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, reduction_rule_id, start_date) VALUES (2, 'REDUCTION', ?, '2026-01-01')", (tk_rule_id,))
    cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, reduction_rule_id, start_date) VALUES (2, 'REDUCTION', ?, '2026-01-01')", (child_rule_id,))
    
    # Scenario 3: Giảng viên thiếu giờ dạy nhưng thừa NCKH lớn (ISI)
    cursor.execute("INSERT INTO teachers (id, name, subject_group, is_female) VALUES (3, 'GV Ghiền NCKH', 'Tự nhiên/Kỹ thuật', 0)")
    cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (3, 'TITLE', 'Giảng viên', '2026-01-01')")
    cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (3, 'DEPARTMENT', 'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học', '2026-01-01')")
    
    # Activity Logs
    # S1: Dạy 300 tiết lý thuyết Đại học, sĩ số 30 -> 300 GC
    cursor.execute("""
        INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity, class_level, class_type, student_count, converted_hours, timeframe_id)
        VALUES (1, ?, '2026-02-01', 300, 'Đại học', 'Lý thuyết', 30, 0, 99)
    """, (teaching_act_id,))
    
    # S2: Dạy lớp đông Đại học, sĩ số 70 (hệ số 1.4). 100 tiết -> 140 GC
    cursor.execute("""
        INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity, class_level, class_type, student_count, converted_hours, timeframe_id)
        VALUES (2, ?, '2026-03-01', 100, 'Đại học', 'Lý thuyết', 70, 0, 99)
    """, (teaching_act_id,))
    
    # S3: Dạy 200 tiết Đại học, sĩ số 30 -> 200 GC. Viết 1 bài ISI -> 1000h NCKH
    cursor.execute("""
        INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity, class_level, class_type, student_count, converted_hours, timeframe_id)
        VALUES (3, ?, '2026-04-01', 200, 'Đại học', 'Lý thuyết', 30, 0, 99)
    """, (teaching_act_id,))
    cursor.execute("""
        INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity, converted_hours, timeframe_id)
        VALUES (3, ?, '2026-04-02', 1, 0, 99)
    """, (nckh_act_id,))
    
    conn.commit()
    conn.close()

def run_qa():
    setup_qa_data()
    df = calculate_teacher_metrics(timeframe_id=99)
    
    print("\n--- QA RESULTS ---")
    
    # Verify S1
    row1 = df[df['id'] == 1].iloc[0]
    print(f"Giảng viên: {row1['name']}")
    print(f"  Định mức gốc GD: {row1['base_gc']}")
    print(f"  Định mức GD thực tế: {row1['dinh_muc_gc_phai_thuc_hien']}")
    print(f"  GD đã thực hiện: {row1['tổng_gc_da_thuc_hien']}")
    print(f"  GD vượt/thiếu: {row1['gc_vuot_thieu_sau_quy_doi']}")
    print(f"  NCKH đã thực hiện: {row1['nckh_da_thuc_hien']} / Yêu cầu: {row1['dinh_muc_nckh_phai_thuc_hien']}")
    
    assert row1['base_gc'] == 270.0
    assert abs(row1['dinh_muc_gc_phai_thuc_hien'] - 270.0) < 0.1
    assert row1['tổng_gc_da_thuc_hien'] == 300.0
    assert abs(row1['gc_vuot_thieu'] - 30.0) < 0.1
    assert row1['dinh_muc_nckh_phai_thuc_hien'] == 600.0
    print("  => GV Binh Thuong assertions passed!")
    print("-" * 20)
    
    # Verify S2
    row2 = df[df['id'] == 2].iloc[0]
    print(f"Giảng viên: {row2['name']}")
    print(f"  Định mức gốc GD: {row2['base_gc']}")
    print(f"  Định mức GD thực tế: {row2['dinh_muc_gc_phai_thuc_hien']}")
    print(f"  Giờ miễn giảm thêm (con nhỏ): {row2['so_gio_duoc_mien_giam']}")
    print(f"  GD đã thực hiện: {row2['tổng_gc_da_thuc_hien']}")
    print(f"  GD vượt/thiếu: {row2['gc_vuot_thieu_sau_quy_doi']}")
    print(f"  NCKH đã thực hiện: {row2['nckh_da_thuc_hien']} / Yêu cầu: {row2['dinh_muc_nckh_phai_thuc_hien']}")
    
    assert row2['base_gc'] == 270.0
    assert abs(row2['dinh_muc_gc_phai_thuc_hien'] - 162.0) < 0.1  # 270 * (1 - 40%)
    assert abs(row2['so_gio_duoc_mien_giam'] - 16.2) < 0.1  # 162 * 10%
    assert row2['tổng_gc_da_thuc_hien'] == 140.0  # 100 * 1.4
    # NCKH required: 600 * (1 - 30%) = 420.0 (as defined in seed_reductions.py for Nữ nuôi con nhỏ 12-36 tháng)
    assert abs(row2['dinh_muc_nckh_phai_thuc_hien'] - 420.0) < 0.1
    print("  => Truong Khoa Nu assertions passed!")
    print("-" * 20)
    
    # Verify S3
    row3 = df[df['id'] == 3].iloc[0]
    print(f"Giảng viên: {row3['name']}")
    print(f"  Định mức gốc GD: {row3['base_gc']}")
    print(f"  Định mức GD thực tế: {row3['dinh_muc_gc_phai_thuc_hien']}")
    print(f"  GD đã thực hiện: {row3['tổng_gc_da_thuc_hien']}")
    print(f"  GD vượt/thiếu: {row3['gc_vuot_thieu_sau_quy_doi']}")
    print(f"  NCKH đã thực hiện: {row3['nckh_da_thuc_hien']} / Yêu cầu: {row3['dinh_muc_nckh_phai_thuc_hien']}")
    
    assert row3['base_gc'] == 270.0
    assert abs(row3['dinh_muc_gc_phai_thuc_hien'] - 270.0) < 0.1
    assert row3['tổng_gc_da_thuc_hien'] == 200.0
    assert row3['nckh_da_thuc_hien'] == 1000.0
    assert row3['dinh_muc_nckh_phai_thuc_hien'] == 600.0
    print("  => GV Ghien NCKH assertions passed!")
    print("-" * 20)
    
    print("\n🎉 ALL QA INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_qa()
    finally:
        # Clean up database file
        if os.path.exists('test_qa.sqlite'):
            try:
                os.remove('test_qa.sqlite')
            except Exception:
                pass
