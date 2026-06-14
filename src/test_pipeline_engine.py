import pytest
import pandas as pd
import os
import io
import openpyxl
from database import init_db, seed_initial_data, get_connection
from pipeline import parse_excel_to_df, sanitize_value
from pipeline.validator import validate_teachers_data, validate_activities_data, validate_schedule_data
from pipeline.differ import diff_teachers, diff_activities, diff_schedule

def test_cell_sanitizer():
    assert sanitize_value("=SUM(A1:A5)") == "'=SUM(A1:A5)"
    assert sanitize_value("+12345") == "'+12345"
    assert sanitize_value("-abc") == "'-abc"
    assert sanitize_value("@admin") == "'@admin"
    assert sanitize_value("Hello World") == "Hello World"
    assert sanitize_value(123) == 123
    assert sanitize_value(None) is None

def test_importer_and_diff_pipeline(tmp_path):
    test_db = os.path.join(tmp_path, "test_pipeline.sqlite")
    os.environ["DB_PATH"] = test_db
    
    init_db()
    seed_initial_data()
    
    conn = get_connection()
    
    # 1. Teachers diff & validation test
    teachers_df = pd.DataFrame([
        {
            "Mã GV": "1",
            "Họ tên": "Nguyễn Văn A",
            "Tổ bộ môn": "Bộ môn Toán",
            "Nữ": "Không",
            "Loại hợp đồng": "TEACHER",
            "Học hàm học vị": "TS",
            "Cấp bậc quân hàm": "Đại tá",
            "Chức danh": "Giảng viên",
            "Chức vụ": "",
            "Ngày bổ nhiệm chức vụ": "",
            "Ngày bổ nhiệm chức danh": "",
            "Đơn vị": "Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học"
        },
        {
            "Mã GV": "2",
            "Họ tên": "Trần Thị B",
            "Tổ bộ môn": "Bộ môn Lý",
            "Nữ": "Có",
            "Loại hợp đồng": "INVALID_ROLE", # invalid contract type
            "Học hàm học vị": "",
            "Cấp bậc quân hàm": "",
            "Chức danh": "",
            "Chức vụ": "",
            "Ngày bổ nhiệm chức vụ": "",
            "Ngày bổ nhiệm chức danh": "",
            "Đơn vị": "Nonexistent Department" # invalid dept
        }
    ])
    
    errs = validate_teachers_data(teachers_df, conn)
    assert len(errs) > 0
    # The second row has 2 validation errors: invalid contract type and nonexistent department
    err_rows = [e[0] for e in errs]
    assert 1 in err_rows # index 1 corresponds to second row

    # Correct second row
    teachers_df.at[1, "Loại hợp đồng"] = "TEACHER"
    teachers_df.at[1, "Đơn vị"] = "Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học"
    errs = validate_teachers_data(teachers_df, conn)
    assert len(errs) == 0

    diffed = diff_teachers(teachers_df, conn)
    # Both are new
    assert diffed.iloc[0]["diff_marker"] == "NEW"
    conn.close()

def test_ghost_rows_and_null_validations(tmp_path):
    from pipeline.importer import drop_ghost_rows
    
    # 1. Test drop_ghost_rows
    # Row 0: valid data
    # Row 1: ghost row (has metadata but all other columns are NaN or empty)
    # Row 2: ghost row (completely NaN)
    df = pd.DataFrame([
        {
            "Đơn vị": "Bộ môn Toán",
            "Mã GV": "101",
            "Họ tên": "Teacher A",
            "Chức vụ": "Trưởng bộ môn"
        },
        {
            "Đơn vị": "Bộ môn Toán",
            "Mã GV": None,
            "Họ tên": "",
            "Chức vụ": "nan"  # will be sanitized to None in sanitize_value, but here we test drop_ghost_rows directly with None/empty
        },
        {
            "Đơn vị": None,
            "Mã GV": None,
            "Họ tên": None,
            "Chức vụ": None
        }
    ])
    
    # Pre-clean the empty strings/nan values as the importer would
    df = df.map(sanitize_value)
    
    cleaned_df = drop_ghost_rows(df)
    assert len(cleaned_df) == 1
    assert cleaned_df.iloc[0]["Họ tên"] == "Teacher A"

    # 2. Test validators return clean error messages without 'nan' or 'None'
    test_db = os.path.join(tmp_path, "test_pipeline_2.sqlite")
    os.environ["DB_PATH"] = test_db
    init_db()
    seed_initial_data()
    conn = get_connection()

    # Invalid Activities dataframe with missing values
    act_df = pd.DataFrame([
        {
            "Mã GV": None, # Missing required
            "Tên loại hoạt động": "", # Missing required
            "Ngày thực hiện": None, # Missing required
            "Số lượng": None # Missing required
        },
        {
            "Mã GV": "9999", # Nonexistent
            "Tên loại hoạt động": "NCKH",
            "Ngày thực hiện": "invalid-date",
            "Số lượng": -5 # Invalid negative
        }
    ])
    
    act_df = act_df.map(sanitize_value)
    act_errors = validate_activities_data(act_df, conn)
    
    # Make sure we don't have 'nan' or 'None' string representation in the error messages
    for idx, row_num, msg in act_errors:
        assert "None" not in msg
        assert "nan" not in msg
        assert "NaN" not in msg
        
    # Check specific messages for row 0
    row_0_errors = [msg for idx, row_num, msg in act_errors if idx == 0]
    assert "Mã GV không được để trống." in row_0_errors
    assert "Tên loại hoạt động không được để trống." in row_0_errors
    assert "Ngày thực hiện không được để trống." in row_0_errors
    assert "Số lượng không được để trống." in row_0_errors
    
    # Check specific messages for row 1
    row_1_errors = [msg for idx, row_num, msg in act_errors if idx == 1]
    assert "Mã GV '9999' không tồn tại trong hệ thống." in row_1_errors
    assert "Ngày thực hiện 'invalid-date' không đúng định dạng YYYY-MM-DD." in row_1_errors
    assert "Số lượng '-5.0' phải là số dương lớn hơn 0." in row_1_errors

    # Invalid Schedule dataframe with missing values
    sched_df = pd.DataFrame([
        {
            "Mã GV (Khóa)": None,
            "Họ tên (Khóa)": "Teacher A",
            "Chức danh (Khóa)": "Giảng viên",
            "Đơn vị (Khóa)": "Toán",
            "Tên môn học": "",
            "Loại": None,
            "Nhóm": "",
            "Sỉ số": None,
            "Tiết quy đổi": None,
            "Hệ số tín chỉ": None,
            "Ghi chú": ""
        }
    ])
    
    sched_df = sched_df.map(sanitize_value)
    sched_errors = validate_schedule_data(sched_df, conn)
    for idx, row_num, msg in sched_errors:
        assert "None" not in msg
        assert "nan" not in msg
        
    sched_msg = [msg for idx, row_num, msg in sched_errors]
    assert "Mã GV không được để trống." in sched_msg
    
    conn.close()

