import pandas as pd
from database import get_connection
from .templates import ALLOWED_LOAI

ALLOWED_LOAI_SET = set(ALLOWED_LOAI)

def safe_float(val):
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if val_str == "" or val_str.lower() == "nan":
        return None
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
    errors = []

    try:
        df = pd.read_excel(file_bytes, header=3)
    except Exception as e:
        return False, [f"Không thể đọc file Excel: {str(e)}"], None

    df = df.dropna(how='all').reset_index(drop=True)
    if df.empty:
        return False, ["File Excel không có dữ liệu."], None

    expected_headers = [
        "Mã GV (Khóa)", "Họ tên (Khóa)", "Chức danh (Khóa)", "Đơn vị (Khóa)",
        "Tên môn học", "Loại", "Nhóm", "Sỉ số", "Tiết quy đổi",
        "Hệ số tín chỉ", "Ghi chú"
    ]
    actual_headers = [str(h).strip() if not pd.isna(h) else "" for h in df.columns]
    if len(actual_headers) < 11:
        return False, [f"Cần 11 cột, phát hiện {len(actual_headers)} cột."], None

    for i in range(11):
        if actual_headers[i] != expected_headers[i]:
            errors.append(
                f"Cột thứ {i+1} không khớp. "
                f"Yêu cầu: '{expected_headers[i]}', Thực tế: '{actual_headers[i]}'"
            )
    if errors:
        return False, errors, None

    df.columns = [
        "teacher_id", "teacher_name", "chuc_danh", "don_vi",
        "subject_name", "loai", "nhom", "si_so", "tiet_quy_doi",
        "he_so_tin_chi", "ghi_chu"
    ]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM teachers")
    db_teachers = {t['id']: t['name'] for t in cursor.fetchall()}
    conn.close()

    for idx, row in df.iterrows():
        row_num = idx + 5

        t_id_raw = row['teacher_id']
        if pd.isna(t_id_raw) or str(t_id_raw).strip() == "":
            errors.append(f"Dòng {row_num}: Mã GV bị trống.")
            continue

        try:
            t_id = int(float(t_id_raw))
            df.at[idx, 'teacher_id'] = t_id
        except (ValueError, TypeError):
            errors.append(f"Dòng {row_num}: Mã GV '{t_id_raw}' phải là số nguyên.")
            continue

        if t_id not in db_teachers:
            errors.append(f"Dòng {row_num}: Mã GV {t_id} không tồn tại trong hệ thống.")

        subject_name = row.get('subject_name', '')
        if pd.isna(subject_name) or str(subject_name).strip() == "":
            errors.append(f"Dòng {row_num}: Tên môn học bị trống.")

        loai = row.get('loai', '')
        if pd.isna(loai) or str(loai).strip() == "":
            errors.append(f"Dòng {row_num}: Cột Loại bị trống.")
        else:
            loai_clean = str(loai).strip().upper()
            if loai_clean not in ALLOWED_LOAI_SET:
                allowed_str = ", ".join(ALLOWED_LOAI)
                errors.append(
                    f"Dòng {row_num}: Loại '{loai}' không hợp lệ. "
                    f"Chấp nhận: {allowed_str}"
                )
            else:
                df.at[idx, 'loai'] = loai_clean

        si_so_raw = row.get('si_so', None)
        si_so_val = safe_float(si_so_raw)
        if si_so_val is None:
            errors.append(f"Dòng {row_num}: Sỉ số bị trống hoặc không phải số.")
        elif si_so_val < 0:
            errors.append(f"Dòng {row_num}: Sỉ số không được âm ({si_so_val}).")
        elif not si_so_val.is_integer():
            errors.append(f"Dòng {row_num}: Sỉ số phải là số nguyên ({si_so_val}).")
        else:
            df.at[idx, 'si_so'] = int(si_so_val)

        tqđ_raw = row.get('tiet_quy_doi', None)
        tqđ_val = safe_float(tqđ_raw)
        if tqđ_val is None:
            errors.append(f"Dòng {row_num}: Tiết quy đổi bị trống hoặc không phải số.")
        elif tqđ_val < 0:
            errors.append(f"Dòng {row_num}: Tiết quy đổi không được âm ({tqđ_val}).")
        else:
            df.at[idx, 'tiet_quy_doi'] = tqđ_val

        hstc_raw = row.get('he_so_tin_chi', None)
        hstc_val = safe_float(hstc_raw)
        if hstc_val is None:
            errors.append(f"Dòng {row_num}: Hệ số tín chỉ bị trống hoặc không phải số.")
        elif hstc_val <= 0:
            errors.append(f"Dòng {row_num}: Hệ số tín chỉ phải > 0 ({hstc_val}).")
        else:
            df.at[idx, 'he_so_tin_chi'] = hstc_val

    if errors:
        return False, errors, df

    return True, [], df
