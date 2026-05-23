import pandas as pd
from database import get_connection

def safe_float(val):
    if pd.isna(val) or val is None:
        return 0.0
    val_str = str(val).strip()
    if val_str == "" or val_str.lower() == "nan":
        return 0.0
    val_str = val_str.replace(" ", "")
    if "," in val_str and "." not in val_str:
        val_str = val_str.replace(",", ".")
    elif "," in val_str and "." in val_str:
        if val_str.find(".") < val_str.find(","):
            val_str = val_str.replace(".", "").replace(",", ".")
        else:
            val_str = val_str.replace(",", "")
    return float(val_str)

def validate_excel_data(file_bytes):
    """
    Đọc dữ liệu từ file Excel và thực hiện kiểm tra tính hợp lệ.
    Trả về: (is_valid, list_of_errors, parsed_df)
    """
    errors = []
    
    # 1. Đọc Excel
    try:
        df = pd.read_excel(file_bytes, header=3)
    except Exception as e:
        return False, [f"Không thể đọc file Excel. Chi tiết lỗi: {str(e)}"], None
        
    if df.empty:
        return False, ["File Excel không có dữ liệu để nhập."], None

    df = df.dropna(how='all')
    
    # 2. Kiểm tra cột tiêu đề
    expected_headers = [
        "Mã GV (Khóa)", 
        "Họ tên (Khóa)", 
        "Giảng dạy trực tiếp*", 
        "HĐ chuyên môn & Bồi dưỡng*", 
        "NCKH*", 
        "Nhiệm vụ khác*", 
        "Ghi chú"
    ]
    
    actual_headers = list(df.columns)
    if len(actual_headers) < 6:
        return False, [f"Cấu trúc file không đúng. Cần tối thiểu 6 cột dữ liệu đầu tiên."], None
        
    for i in range(6):
        if actual_headers[i].strip() != expected_headers[i]:
            errors.append(f"Tên cột thứ {i+1} không khớp. Yêu cầu: '{expected_headers[i]}', Thực tế: '{actual_headers[i]}'")
            
    if errors:
        return False, errors, None
        
    df.columns = [
        "teacher_id", "teacher_name", "giang_day_truc_tiep", 
        "hdcm_bd", "nckh_total", "nvk_total"
    ] + list(df.columns[6:])
    
    # 3. Kết nối DB lấy danh sách Mã GV hiện tại để đối chiếu
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM teachers")
    db_teachers = {t['id']: t['name'] for t in cursor.fetchall()}
    conn.close()
    
    # 4. Kiểm tra từng dòng
    seen_ids = set()
    
    for idx, row in df.iterrows():
        row_num = idx + 5
        
        # A. Kiểm tra Mã GV trống
        t_id_raw = row['teacher_id']
        if pd.isna(t_id_raw) or str(t_id_raw).strip() == "":
            errors.append(f"Dòng {row_num}: Mã GV bị trống.")
            continue
            
        try:
            t_id_float = float(t_id_raw)
            if t_id_float.is_integer():
                t_id = int(t_id_float)
            else:
                errors.append(f"Dòng {row_num}: Mã GV '{t_id_raw}' phải là số nguyên.")
                continue
            df.at[idx, 'teacher_id'] = t_id
        except ValueError:
            errors.append(f"Dòng {row_num}: Mã GV '{t_id_raw}' phải là số nguyên.")
            continue
            
        # B. Kiểm tra trùng lặp Mã GV trong file
        if t_id in seen_ids:
            errors.append(f"Dòng {row_num}: Trùng lặp Mã GV {t_id} trong file.")
        seen_ids.add(t_id)
        
        # C. Kiểm tra Mã GV tồn tại trong DB
        if t_id not in db_teachers:
            errors.append(f"Dòng {row_num}: Mã GV {t_id} không tồn tại trong hệ thống.")
            continue
            
        # D. Kiểm tra giá trị số
        for friendly_name, col_name in [
            ("Giảng dạy trực tiếp", "giang_day_truc_tiep"),
            ("HĐ chuyên môn & Bồi dưỡng", "hdcm_bd"),
            ("NCKH", "nckh_total"),
            ("Nhiệm vụ khác", "nvk_total")
        ]:
            val = row[col_name]
            try:
                cleaned_val = safe_float(val)
                if cleaned_val < 0:
                    errors.append(f"Dòng {row_num}: Cột '{friendly_name}' có giá trị âm ({cleaned_val}). Phải là số >= 0.")
                df.at[idx, col_name] = cleaned_val
            except ValueError:
                errors.append(f"Dòng {row_num}: Cột '{friendly_name}' có giá trị '{val}' không phải là số hợp lệ.")
                    
    if errors:
        return False, errors, df
        
    return True, [], df
