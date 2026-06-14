import os
from database import init_db, seed_initial_data, get_connection
from pipeline.validator import validate_teachers_data
import pandas as pd

# Set database path
os.environ["DB_PATH"] = "test_pipeline_debug.sqlite"
if os.path.exists("test_pipeline_debug.sqlite"):
    os.remove("test_pipeline_debug.sqlite")

init_db()
seed_initial_data()

conn = get_connection()

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
        "Ngày bổ nhiệm": "",
        "Đơn vị": "Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học"
    },
    {
        "Mã GV": "2",
        "Họ tên": "Trần Thị B",
        "Tổ bộ môn": "Bộ môn Lý",
        "Nữ": "Có",
        "Loại hợp đồng": "INVALID_ROLE",
        "Học hàm học vị": "",
        "Cấp bậc quân hàm": "",
        "Chức danh": "",
        "Chức vụ": "",
        "Ngày bổ nhiệm": "",
        "Đơn vị": "Nonexistent Department"
    }
])

errs = validate_teachers_data(teachers_df, conn)
print("Errors found:")
for e in errs:
    print(e)

conn.close()
if os.path.exists("test_pipeline_debug.sqlite"):
    os.remove("test_pipeline_debug.sqlite")
