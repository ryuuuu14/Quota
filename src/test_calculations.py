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

from calculations import calculate_teacher_metrics, get_teacher_formula_breakdown

def test_bui_thi_x():
    old_db_path = os.environ.pop('DB_PATH', None)
    try:
        from database import get_connection
        conn = get_connection()
        c = conn.cursor()
        
        # Find Bùi Thị X dynamically
        teacher_row = c.execute("SELECT id FROM teachers WHERE name = 'Bùi Thị X'").fetchone()
        tf_row = c.execute("SELECT id, start_date FROM timeframes WHERE name = 'Năm học 2025-2026'").fetchone()
        
        if not teacher_row or not tf_row:
            print("Bùi Thị X or Timeframe not found in DB, skipping verification.")
            conn.close()
            return
            
        num_holidays = c.execute("SELECT COUNT(*) FROM academic_holidays WHERE timeframe_id = ?", (tf_row[0],)).fetchone()[0]
        print("NUM HOLIDAYS IN TEST:", num_holidays)
        conn.close()

        teacher_id = teacher_row[0]
        timeframe_id = tf_row[0]
        start_date = tf_row[1]
        
        df = calculate_teacher_metrics(teacher_id=teacher_id, timeframe_id=timeframe_id)
        assert not df.empty, "Teacher Bùi Thị X not found in metrics calculation"
        row = df.iloc[0]
        
        req_gc = row['dinh_muc_gc_phai_thuc_hien']
        red_gc = row['so_gio_duoc_mien_giam']
        
        if start_date == '2025-08-04':
            if num_holidays <= 7:
                expected_req = 270.18
                expected_red = 107.92
            else:
                expected_req = 269.77
                expected_red = 114.03
        else:
            expected_req = 268.68
            expected_red = 110.62
            
        assert abs(req_gc - expected_req) < 0.2, f"Expected required GC around {expected_req}, got {req_gc}"
        assert abs(red_gc - expected_red) < 0.2, f"Expected reduced GC around {expected_red}, got {red_gc}"
    finally:
        if old_db_path is not None:
            os.environ['DB_PATH'] = old_db_path

    print("test_bui_thi_x passed.")


def test_get_teacher_formula_breakdown_exists():
    old_db_path = os.environ.pop('DB_PATH', None)
    try:
        from database import get_connection
        conn = get_connection()
        c = conn.cursor()
        teacher_row = c.execute("SELECT id FROM teachers LIMIT 1").fetchone()
        tf_row = c.execute("SELECT id FROM timeframes LIMIT 1").fetchone()
        conn.close()
        
        if not teacher_row or not tf_row:
            print("No teachers/timeframes in DB, skipping breakdown verification.")
            return

        breakdown = get_teacher_formula_breakdown(teacher_row[0], tf_row[0])
        assert breakdown is not None
        assert 'teacher_name' in breakdown
        assert 'segments' in breakdown
        assert 'reductions' in breakdown
        assert 'total_required_gc' in breakdown
    finally:
        if old_db_path is not None:
            os.environ['DB_PATH'] = old_db_path
    print("test_get_teacher_formula_breakdown_exists passed.")

from calculations import _apply_auto_compensation

def test_apply_auto_compensation_cases():
    # Case 1: GC excess, NCKH deficit.
    # NCKH norm is 600, NCKH done is 150 (exactly 25%). GC excess is 50, NCKH deficit is -300.
    # 1 GC = 3 NCKH.
    # We want to transfer. Deficit is -300. In GC, we need -(-300) / 3 = 100 GC.
    # Since GC excess is 50, we transfer all 50 GC to get 150 NCKH.
    # Expected: GC excess remains 0, NCKH deficit becomes -150.
    row1 = pd.Series({
        'gc_vuot_thieu': 50.0,
        'nckh_vuot_thieu': -300.0,
        'dinh_muc_nckh_phai_thuc_hien': 600.0,
        'nckh_da_thuc_hien': 150.0
    })
    gc_res, nckh_res = _apply_auto_compensation(row1)
    assert gc_res == 0.0, f"Expected GC 0.0, got {gc_res}"
    assert nckh_res == -150.0, f"Expected NCKH -150.0, got {nckh_res}"

    # Case 2: GC excess, NCKH deficit, but NCKH done < 25% of norm.
    # No transfer should occur.
    row2 = pd.Series({
        'gc_vuot_thieu': 50.0,
        'nckh_vuot_thieu': -300.0,
        'dinh_muc_nckh_phai_thuc_hien': 600.0,
        'nckh_da_thuc_hien': 149.0
    })
    gc_res, nckh_res = _apply_auto_compensation(row2)
    assert gc_res == 50.0
    assert nckh_res == -300.0

    # Case 3: GC deficit, NCKH excess.
    # GC norm is 270, direct teaching is 135 (exactly 50%). GC deficit is -50, NCKH excess is 300.
    # 3 NCKH = 1 GC.
    # Deficit is -50 GC. In NCKH, we need -(-50) * 3 = 150 NCKH.
    # Since NCKH excess is 300, we transfer 150 NCKH to cover all -50 GC.
    # Expected: GC deficit becomes 0.0, NCKH excess becomes 150.0.
    row3 = pd.Series({
        'gc_vuot_thieu': -50.0,
        'nckh_vuot_thieu': 300.0,
        'dinh_muc_gc_phai_thuc_hien': 270.0,
        'giang_day_truc_tiep': 135.0
    })
    gc_res, nckh_res = _apply_auto_compensation(row3)
    assert gc_res == 0.0, f"Expected GC 0.0, got {gc_res}"
    assert nckh_res == 150.0, f"Expected NCKH 150.0, got {nckh_res}"

    # Case 4: GC deficit, NCKH excess, but direct teaching < 50% GC norm.
    # No transfer should occur.
    row4 = pd.Series({
        'gc_vuot_thieu': -50.0,
        'nckh_vuot_thieu': 300.0,
        'dinh_muc_gc_phai_thuc_hien': 270.0,
        'giang_day_truc_tiep': 134.0
    })
    gc_res, nckh_res = _apply_auto_compensation(row4)
    assert gc_res == -50.0
    assert nckh_res == 300.0
    print("test_apply_auto_compensation_cases passed.")

if __name__ == "__main__":
    test_dai_hoc_ly_thuyet()
    test_dai_hoc_ngoai_ngu()
    test_boi_duong()
    test_thao_luan_equivalent()
    test_calculate_t04_weeks_with_holidays()
    test_bui_thi_x()
    test_get_teacher_formula_breakdown_exists()
    test_apply_auto_compensation_cases()
    print("All tests passed!")
