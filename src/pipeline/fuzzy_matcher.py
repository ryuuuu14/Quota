import difflib

SYNONYMS = {
    "Mã GV": ["msgv", "ma gv", "ma_giang_vien", "magv", "mã giảng viên", "mã cán bộ", "macb", "ma cb", "mã gv (khóa)"],
    "Họ tên": ["ho ten", "ho_ten", "fullname", "name", "họ tên", "tên", "tên nhà giáo", "nhà giáo", "họ và tên", "họ tên (khóa)"],
    "Tên loại hoạt động": ["hoat dong", "loai hoat dong", "tên hoạt động", "hoạt động", "loại hoạt động"],
    "Ngày thực hiện": ["ngay", "ngay thực hiện", "ngày thực hiện", "ngày", "date", "log date", "ngay_thuc_hien"],
    "Số lượng": ["so luong", "qty", "quantity", "số lượng", "số giờ", "hours", "so_luong"],
    "Cấp lớp": ["cap lop", "cấp lớp", "trình độ", "hệ đào tạo", "bậc đào tạo", "cấp/lớp"],
    "Loại lớp": ["loai lop", "loại hình", "hình thức", "loại lớp", "class_type"],
    "Số học viên": ["si so", "sĩ số", "số sv", "sv", "học viên", "số học viên", "so_hoc_vien", "student count", "sỉ số"],
    "Cấp đề tài": ["cap de tai", "cấp đề tài", "cấp", "cấp nckh", "nckh level", "cấp đề tài/bài báo"],
    "Tác giả chính": ["main author", "is main", "tác giả chính", "tg chính", "vai trò"],
    "Giảng dạy tiếng nước ngoài": ["foreign language", "tiếng nước ngoài", "dạy tiếng anh", "dạy bằng tiếng nước ngoài"],
    "Ghi chú": ["note", "ghi chu", "ghi chú", "description", "mô tả"],
    # For Schedule
    "Mã GV (Khóa)": ["msgv", "ma gv", "ma_giang_vien", "magv", "mã giảng viên", "mã gv", "mã gv (khóa)"],
    "Họ tên (Khóa)": ["ho ten", "ho_ten", "fullname", "name", "họ tên", "họ và tên", "họ tên (khóa)"],
    "Chức danh (Khóa)": ["chuc danh", "chức danh", "chức danh (khóa)"],
    "Đơn vị (Khóa)": ["don vi", "đơn vị", "đơn vị (khóa)"],
    "Tên môn học": ["mon hoc", "tên môn học", "môn học", "subject", "tên môn"],
    "Loại": ["loai", "loại", "loại môn", "loại hình"],
    "Nhóm": ["nhom", "nhóm", "group", "class group"],
    "Sỉ số": ["si so", "sĩ số", "số sv", "sv", "học viên", "sĩ số lớp"],
    "Tiết quy đổi": ["tiet quy doi", "tiết quy đổi", "tiết quy đổi", "giờ quy đổi", "gc quy đổi"],
    "Hệ số tín chỉ": ["he so tin chi", "hệ số tín chỉ", "tín chỉ", "credits"],
    # For Overrides
    "Tổng GC thực hiện": ["tong gc", "tổng gc thực hiện", "tổng giờ chuẩn", "tổng gc đã thực hiện", "tong_gc_da_thuc_hien", "tổng gc"],
    "NCKH thực hiện": ["nckh", "nckh thực hiện", "nckh đã thực hiện", "giờ nckh", "nckh_da_thuc_hien", "nckh"],
    "Số giờ miễn giảm": ["mien giam", "số giờ miễn giảm", "giờ miễn giảm", "miễn giảm", "so_gio_duoc_mien_giam", "miễn giảm gc"],
    "Định mức GC": ["dinh muc", "định mức gc", "định mức", "dinh_muc_gc_phai_thuc_hien", "định mức giảng dạy"]
}

def normalize_string(s: str) -> str:
    if not s:
        return ""
    # Lowercase, strip whitespace, remove punctuation and common symbols
    s = str(s).lower().strip()
    # Normalize unicode to decompose accents if possible (optional simple normalization)
    import unicodedata
    s = u"".join([c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)])
    return s.replace("_", " ").replace("-", " ")

def fuzzy_match_columns(excel_headers: list, expected_columns: list) -> dict:
    """
    Maps each expected column to the best matching Excel header.
    Returns: dict of {expected_column: excel_header_or_None}
    """
    mappings = {}
    normalized_excel_headers = {normalize_string(h): h for h in excel_headers if h}

    for expected in expected_columns:
        norm_expected = normalize_string(expected)
        
        # 1. Direct exact or normalized match
        if norm_expected in normalized_excel_headers:
            mappings[expected] = normalized_excel_headers[norm_expected]
            continue

        # 2. Check synonyms
        syns = SYNONYMS.get(expected, [])
        found_syn = False
        for syn in syns:
            norm_syn = normalize_string(syn)
            if norm_syn in normalized_excel_headers:
                mappings[expected] = normalized_excel_headers[norm_syn]
                found_syn = True
                break
        
        if found_syn:
            continue

        # 3. Fallback to difflib get_close_matches on normalized strings
        matches = difflib.get_close_matches(norm_expected, list(normalized_excel_headers.keys()), n=1, cutoff=0.5)
        if matches:
            mappings[expected] = normalized_excel_headers[matches[0]]
            continue
            
        # 4. Fallback search inside synonym lists with close matches
        for syn in syns:
            norm_syn = normalize_string(syn)
            matches = difflib.get_close_matches(norm_syn, list(normalized_excel_headers.keys()), n=1, cutoff=0.6)
            if matches:
                mappings[expected] = normalized_excel_headers[matches[0]]
                found_syn = True
                break
        
        if not found_syn:
            mappings[expected] = None

    return mappings


def suggest_mappings(excel_headers: list, expected_columns: list) -> dict:
    """
    Alias for fuzzy_match_columns used by the UI page.
    """
    return fuzzy_match_columns(excel_headers, expected_columns)
