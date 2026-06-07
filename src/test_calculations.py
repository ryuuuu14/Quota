import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from calculations import calculate_activity_hours

def test_dai_hoc_ly_thuyet():
    log_row = {
        'quantity': 10,
        'class_level': 'Đại học',
        'class_type': 'Lý thuyết',
        'student_count': 50
    }
    activity_type_row = {
        'category': 'Giảng dạy',
        'is_teaching_activity': 1,
        'base_conversion_rate': 1.0
    }
    
    val = calculate_activity_hours(log_row, activity_type_row)
    assert val == 12.0, f"Expected 12.0, got {val}"
    print("test_dai_hoc_ly_thuyet passed.")

def test_dai_hoc_ngoai_ngu():
    log_row = {
        'quantity': 10,
        'class_level': 'Đại học',
        'class_type': 'Ngoại ngữ/CNTT',
        'student_count': 30
    }
    activity_type_row = {
        'category': 'Giảng dạy',
        'is_teaching_activity': 1,
        'base_conversion_rate': 1.0
    }
    
    val = calculate_activity_hours(log_row, activity_type_row)
    assert val == 12.0, f"Expected 12.0, got {val}"
    print("test_dai_hoc_ngoai_ngu passed.")

def test_boi_duong():
    log_row = {
        'quantity': 10,
        'class_level': 'Bồi dưỡng',
        'student_count': 100
    }
    activity_type_row = {
        'category': 'Giảng dạy',
        'is_teaching_activity': 1,
        'base_conversion_rate': 1.5
    }
    
    val = calculate_activity_hours(log_row, activity_type_row)
    assert val == 15.0, f"Expected 15.0, got {val}"
    print("test_boi_duong passed.")

def test_thao_luan_equivalent():
    log_row = {
        'quantity': 10,
        'class_level': 'Đại học',
        'class_type': 'Thảo luận',
        'student_count': 50
    }
    activity_type_row = {
        'category': 'Giảng dạy',
        'is_teaching_activity': 1,
        'base_conversion_rate': 1.0
    }
    
    val = calculate_activity_hours(log_row, activity_type_row)
    assert val == 12.0, f"Expected 12.0, got {val}"
    print("test_thao_luan_equivalent passed.")

from calculations import calculate_t04_weeks
import pandas as pd

def test_calculate_t04_weeks_with_holidays():
    # Scenario: 28 days (4 calendar weeks)
    start_date = pd.to_datetime("2026-02-01")
    end_date = pd.to_datetime("2026-03-01")
    
    # Without holidays
    w_no_h = calculate_t04_weeks(start_date, end_date)
    assert w_no_h == 4.0, f"Expected 4.0, got {w_no_h}"
    
    # With a 7-day holiday
    holidays = [(pd.to_datetime("2026-02-10"), pd.to_datetime("2026-02-16"))]
    w_h = calculate_t04_weeks(start_date, end_date, holidays)
    # Remaining active days = 28 - 7 = 21 days
    # 21 days // 7 = 3 weeks, rem 0 -> 3.0 weeks
    assert w_h == 3.0, f"Expected 3.0, got {w_h}"
    print("test_calculate_t04_weeks_with_holidays passed.")

from calculations import calculate_teacher_metrics

def test_bui_thi_x():
    old_db_path = os.environ.pop('DB_PATH', None)
    try:
        from database import get_connection
        conn = get_connection()
        c = conn.cursor()
        
        # Find Bùi Thị X dynamically
        teacher_row = c.execute("SELECT id FROM teachers WHERE name = 'Bùi Thị X'").fetchone()
        tf_row = c.execute("SELECT id, start_date FROM timeframes WHERE name = 'Năm học 2025-2026'").fetchone()
        conn.close()
        
        if not teacher_row or not tf_row:
            print("Bùi Thị X or Timeframe not found in DB, skipping verification.")
            return

        teacher_id = teacher_row[0]
        timeframe_id = tf_row[0]
        start_date = tf_row[1]
        
        df = calculate_teacher_metrics(teacher_id=teacher_id, timeframe_id=timeframe_id)
        assert not df.empty, "Teacher Bùi Thị X not found in metrics calculation"
        row = df.iloc[0]
        
        req_gc = row['dinh_muc_gc_phai_thuc_hien']
        red_gc = row['so_gio_duoc_mien_giam']
        
        if start_date == '2025-08-04':
            expected_req = 270.71
            expected_red = 112.76
        else:
            expected_req = 268.68
            expected_red = 110.62
            
        assert abs(req_gc - expected_req) < 0.1, f"Expected required GC around {expected_req}, got {req_gc}"
        assert abs(red_gc - expected_red) < 0.1, f"Expected reduced GC around {expected_red}, got {red_gc}"
    finally:
        if old_db_path is not None:
            os.environ['DB_PATH'] = old_db_path

    print("test_bui_thi_x passed.")

if __name__ == "__main__":
    test_dai_hoc_ly_thuyet()
    test_dai_hoc_ngoai_ngu()
    test_boi_duong()
    test_thao_luan_equivalent()
    test_calculate_t04_weeks_with_holidays()
    test_bui_thi_x()
    print("All tests passed!")
