import pandas as pd
from datetime import datetime

def safe_float(val):
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if val_str == "" or val_str.lower() == "nan":
        return None
    val_str = val_str.replace(" ", "")
    if "," in val_str and "." not in val_str:
        val_str = val_str.replace(",", ".")
    try:
        return float(val_str)
    except ValueError:
        return None

def parse_bool(val) -> bool:
    if pd.isna(val) or val is None:
        return False
    val_str = str(val).strip().lower()
    return val_str in ("có", "yes", "true", "1", "1.0", "y")

def is_empty_cell(val) -> bool:
    if pd.isna(val) or val is None:
        return True
    val_str = str(val).strip()
    if val_str == "" or val_str.lower() in ("nan", "none"):
        return True
    return False

def validate_teachers_data(df: pd.DataFrame, conn) -> list:
    """
    Validates teacher records and returns a list of error strings per row.
    Format of return: list of (row_idx, row_num, error_message)
    """
    errors = []
    cursor = conn.cursor()
    
    # Pre-fetch lookup tables for validation
    cursor.execute("SELECT rank_name FROM police_ranks")
    valid_ranks = {r["rank_name"].strip().lower() for r in cursor.fetchall()}
    
    cursor.execute("SELECT name FROM departments")
    valid_depts = {d["name"].strip().lower() for d in cursor.fetchall()}
    
    cursor.execute("SELECT name FROM titles")
    valid_titles = {t["name"].strip().lower() for t in cursor.fetchall()}

    expected_cols = [
        "Mã GV", "Họ tên", "Tổ bộ môn", "Nữ", "Loại hợp đồng",
        "Học hàm học vị", "Cấp bậc quân hàm", "Chức danh", 
        "Chức vụ", "Ngày bổ nhiệm chức vụ", "Ngày bổ nhiệm chức danh", "Đơn vị",
        "Thời gian đi học", "Thời gian đi thực tế", "Thời gian nghỉ có phép"
    ]
    
    # Check required columns
    required_cols = ["Mã GV", "Họ tên", "Đơn vị"]
    for col in required_cols:
        if col not in df.columns:
            return [(0, 0, f"Thiếu cột bắt buộc: {col}")]

    # Ensure other optional expected columns exist in dataframe
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    def validate_date_range(range_str):
        if is_empty_cell(range_str):
            return True
        range_str = str(range_str).strip()
        range_str = range_str.replace("to", "-").replace("đến", "-")
        parts = [p.strip() for p in range_str.split("-") if p.strip()]
        if len(parts) > 2 or not parts:
            return False
        for part in parts:
            valid = False
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    datetime.strptime(part, fmt)
                    valid = True
                    break
                except ValueError:
                    continue
            if not valid:
                return False
        return True

    for idx, row in df.iterrows():
        row_num = idx + 5 # standard row start in templates
        
        # Name
        name = row["Họ tên"]
        if is_empty_cell(name):
            errors.append((idx, row_num, "Họ tên không được để trống."))
            
        # Subject group (optional)
        if "Tổ bộ môn" in df.columns:
            grp = row["Tổ bộ môn"]
            if is_empty_cell(grp):
                errors.append((idx, row_num, "Tổ bộ môn không được để trống."))
            
        # Employment type (optional)
        if "Loại hợp đồng" in df.columns:
            emp_raw = row["Loại hợp đồng"]
            if is_empty_cell(emp_raw):
                errors.append((idx, row_num, "Loại hợp đồng không được để trống (Cho phép: TEACHER, STAFF, hoặc GUEST)."))
            else:
                emp = str(emp_raw).strip().upper()
                if emp not in ("TEACHER", "STAFF", "GUEST"):
                    errors.append((idx, row_num, f"Loại hợp đồng '{emp_raw}' không hợp lệ. Phải là: TEACHER, STAFF, hoặc GUEST."))
            
        # Police rank (optional)
        if "Cấp bậc quân hàm" in df.columns:
            rank = row["Cấp bậc quân hàm"]
            if not is_empty_cell(rank):
                if str(rank).strip().lower() not in valid_ranks:
                    errors.append((idx, row_num, f"Cấp bậc quân hàm '{rank}' không tồn tại trong hệ thống."))
                
        # Dept
        dept = row["Đơn vị"]
        if is_empty_cell(dept):
            errors.append((idx, row_num, "Đơn vị không được để trống."))
        elif str(dept).strip().lower() not in valid_depts:
            errors.append((idx, row_num, f"Đơn vị '{dept}' không tồn tại trong hệ thống."))
            
        # Title
        title = row["Chức danh"]
        if not is_empty_cell(title):
            if str(title).strip().lower() not in valid_titles:
                errors.append((idx, row_num, f"Chức danh '{title}' không tồn tại trong hệ thống."))

        # Appointment Date (Role)
        app_date_role = row.get("Ngày bổ nhiệm chức vụ")
        if not is_empty_cell(app_date_role):
            try:
                pd.to_datetime(app_date_role)
            except Exception:
                errors.append((idx, row_num, f"Ngày bổ nhiệm chức vụ '{app_date_role}' không đúng định dạng YYYY-MM-DD."))

        # Appointment Date (Title)
        app_date_title = row.get("Ngày bổ nhiệm chức danh")
        if not is_empty_cell(app_date_title):
            try:
                pd.to_datetime(app_date_title)
            except Exception:
                errors.append((idx, row_num, f"Ngày bổ nhiệm chức danh '{app_date_title}' không đúng định dạng YYYY-MM-DD."))

        # Date range fields
        for field, label in [("Thời gian đi học", "Thời gian đi học"), 
                             ("Thời gian đi thực tế", "Thời gian đi thực tế"), 
                             ("Thời gian nghỉ có phép", "Thời gian nghỉ có phép")]:
            val = row.get(field)
            if not is_empty_cell(val):
                if not validate_date_range(val):
                    errors.append((idx, row_num, f"Trường '{label}' '{val}' không đúng định dạng (Ví dụ: 04/08/2025 - 28/09/2025 hoặc 04/08/2025)."))

    return errors


def validate_activities_data(df: pd.DataFrame, conn) -> list:
    """
    Validates activity log records and returns validation errors.
    """
    errors = []
    cursor = conn.cursor()
    
    # Pre-fetch check data
    cursor.execute("SELECT id FROM teachers")
    valid_teacher_ids = {str(t["id"]) for t in cursor.fetchall()}

    expected_cols = [
        "Mã GV", "Tên loại hoạt động", "Ngày thực hiện", "Số lượng"
    ]
    
    for col in expected_cols:
        if col not in df.columns:
            return [(0, 0, f"Thiếu cột bắt buộc: {col}")]

    for idx, row in df.iterrows():
        # Because we read multiple sheets, row index might not map directly to row + 5
        # but we do our best.
        row_num = idx + 5
        
        t_id_raw = row["Mã GV"]
        if is_empty_cell(t_id_raw):
            errors.append((idx, row_num, "Mã GV không được để trống."))
        else:
            try:
                t_id = str(int(float(str(t_id_raw).strip())))
                if t_id not in valid_teacher_ids:
                    errors.append((idx, row_num, f"Mã GV '{t_id}' không tồn tại trong hệ thống."))
            except ValueError:
                errors.append((idx, row_num, f"Mã GV '{t_id_raw}' không hợp lệ."))

        act_type = row["Tên loại hoạt động"]
        if is_empty_cell(act_type):
            errors.append((idx, row_num, "Tên loại hoạt động không được để trống."))

        log_date = row["Ngày thực hiện"]
        if is_empty_cell(log_date):
            errors.append((idx, row_num, "Ngày thực hiện không được để trống."))
        else:
            try:
                if not isinstance(log_date, datetime):
                    pd.to_datetime(log_date)
            except Exception:
                errors.append((idx, row_num, f"Ngày thực hiện '{log_date}' không đúng định dạng YYYY-MM-DD."))

        qty_raw = row["Số lượng"]
        if is_empty_cell(qty_raw):
            errors.append((idx, row_num, "Số lượng không được để trống."))
        else:
            qty = safe_float(qty_raw)
            if qty is None or qty <= 0:
                errors.append((idx, row_num, f"Số lượng '{qty_raw}' phải là số dương lớn hơn 0."))

    return errors


def validate_schedule_data(df: pd.DataFrame, conn) -> list:
    """
    Validates schedule assignments.
    """
    errors = []
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM teachers")
    valid_ids = {t["id"] for t in cursor.fetchall()}

    expected_cols = [
        "Mã GV (Khóa)", "Họ tên (Khóa)", "Chức danh (Khóa)", "Đơn vị (Khóa)",
        "Tên môn học", "Loại", "Nhóm", "Sỉ số", "Tiết quy đổi",
        "Hệ số tín chỉ", "Ghi chú"
    ]
    
    for col in expected_cols:
        if col not in df.columns:
            return [(0, 0, f"Thiếu cột bắt buộc: {col}")]

    from pipeline.templates import ALLOWED_LOAI
    allowed_loai_set = {l.upper() for l in ALLOWED_LOAI}

    for idx, row in df.iterrows():
        row_num = idx + 5
        
        t_id_raw = row["Mã GV (Khóa)"]
        if is_empty_cell(t_id_raw):
            errors.append((idx, row_num, "Mã GV không được để trống."))
            continue
            
        try:
            t_id = int(float(t_id_raw))
        except Exception:
            errors.append((idx, row_num, f"Mã GV '{t_id_raw}' phải là số nguyên."))
            continue

        if t_id not in valid_ids:
            errors.append((idx, row_num, f"Mã GV {t_id} không tồn tại trong hệ thống."))

        sub = row["Tên môn học"]
        if is_empty_cell(sub):
            errors.append((idx, row_num, "Tên môn học không được để trống."))

        loai_raw = row["Loại"]
        if is_empty_cell(loai_raw):
            errors.append((idx, row_num, "Loại môn học không được để trống."))
        else:
            loai = str(loai_raw).strip().upper()
            if loai not in allowed_loai_set:
                errors.append((idx, row_num, f"Loại '{loai_raw}' không hợp lệ. Cho phép: {', '.join(ALLOWED_LOAI)}."))

        si_so_raw = row["Sỉ số"]
        if is_empty_cell(si_so_raw):
            errors.append((idx, row_num, "Sỉ số không được để trống."))
        else:
            si_so = safe_float(si_so_raw)
            if si_so is None or si_so < 0 or not si_so.is_integer():
                errors.append((idx, row_num, f"Sỉ số '{si_so_raw}' phải là số nguyên không âm."))

        tqđ_raw = row["Tiết quy đổi"]
        if is_empty_cell(tqđ_raw):
            errors.append((idx, row_num, "Tiết quy đổi không được để trống."))
        else:
            tqđ = safe_float(tqđ_raw)
            if tqđ is None or tqđ < 0:
                errors.append((idx, row_num, f"Tiết quy đổi '{tqđ_raw}' phải là số không âm."))

        hstc_raw = row["Hệ số tín chỉ"]
        if is_empty_cell(hstc_raw):
            errors.append((idx, row_num, "Hệ số tín chỉ không được để trống."))
        else:
            hstc = safe_float(hstc_raw)
            if hstc is None or hstc <= 0:
                errors.append((idx, row_num, f"Hệ số tín chỉ '{hstc_raw}' phải > 0."))

    return errors


def validate_aggregate_totals_data(df: pd.DataFrame, conn) -> list:
    """
    Validates aggregate total records and returns validation errors.
    Expected columns: "Mã GV", "Tổng GC thực hiện", "NCKH thực hiện", "Số giờ miễn giảm", "Định mức GC"
    """
    errors = []
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM teachers")
    valid_teacher_ids = {str(t["id"]) for t in cursor.fetchall()}

    expected_cols = [
        "Mã GV", "Tổng GC thực hiện", "NCKH thực hiện", "Số giờ miễn giảm", "Định mức GC"
    ]
    
    for col in expected_cols:
        if col not in df.columns:
            return [(0, 0, f"Thiếu cột bắt buộc: {col}")]

    for idx, row in df.iterrows():
        row_num = idx + 2 # typically row index + 2 in simple spreadsheets
        
        t_id_raw = row["Mã GV"]
        if is_empty_cell(t_id_raw):
            errors.append((idx, row_num, "Mã GV không được để trống."))
        else:
            try:
                t_id = str(int(float(str(t_id_raw).strip())))
                if t_id not in valid_teacher_ids:
                    errors.append((idx, row_num, f"Mã GV '{t_id}' không tồn tại trong hệ thống."))
            except ValueError:
                errors.append((idx, row_num, f"Mã GV '{t_id_raw}' không hợp lệ."))

        # Numeric validations
        for col, label in [
            ("Tổng GC thực hiện", "Tổng GC thực hiện"),
            ("NCKH thực hiện", "NCKH thực hiện"),
            ("Số giờ miễn giảm", "Số giờ miễn giảm"),
            ("Định mức GC", "Định mức GC")
        ]:
            val_raw = row[col]
            if is_empty_cell(val_raw):
                errors.append((idx, row_num, f"{label} không được để trống."))
            else:
                val = safe_float(val_raw)
                if val is None or val < 0:
                    errors.append((idx, row_num, f"{label} '{val_raw}' phải là số không âm."))

    return errors
