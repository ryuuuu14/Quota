import pandas as pd
import json
from database import get_connection
from pipeline.validator import safe_float, parse_bool

def diff_teachers(df: pd.DataFrame, conn) -> pd.DataFrame:
    """
    Compares incoming teachers dataframe with the active database.
    Modifies df to add 'diff_marker' and 'diff_detail' columns.
    """
    cursor = conn.cursor()
    
    # Load all production teachers
    cursor.execute("""
        SELECT t.id, t.name, t.subject_group, t.is_female, t.employment_type, t.guest_rank,
               (SELECT rank_name FROM police_ranks WHERE id = t.police_rank_id) as police_rank,
               (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'TITLE' ORDER BY start_date DESC LIMIT 1) as title,
               (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'DEPARTMENT' ORDER BY start_date DESC LIMIT 1) as dept,
               (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'ROLE' ORDER BY start_date DESC LIMIT 1) as role
        FROM teachers t
    """)
    prod_rows = [dict(r) for r in cursor.fetchall()]
    
    # Map by ID
    prod_map_id = {r["id"]: r for r in prod_rows}
    # Map by name + department for natural key lookup (fallback)
    prod_map = {}
    for r in prod_rows:
        dept_clean = str(r["dept"] or "").strip().lower()
        name_clean = str(r["name"] or "").strip().lower()
        key = (name_clean, dept_clean)
        prod_map[key] = r

    df["diff_marker"] = "NEW"
    df["diff_detail"] = ""

    # Cache police ranks lookup to map rank_name -> ID
    cursor.execute("SELECT id, rank_name FROM police_ranks")
    rank_map = {r["rank_name"].strip().lower(): r["id"] for r in cursor.fetchall()}

    for idx, row in df.iterrows():
        name = str(row["Họ tên"]).strip()
        dept = str(row["Đơn vị"]).strip()
        
        prod = None
        try:
            t_id = int(float(str(row.get("Mã GV", ""))))
            if t_id in prod_map_id:
                prod = prod_map_id[t_id]
        except Exception:
            pass
            
        if not prod:
            key = (name.lower(), dept.lower())
            if key in prod_map:
                prod = prod_map[key]
        
        if prod:
            changes = []
            
            # Check fields
            # 1. Subject group
            new_grp = str(row["Tổ bộ môn"]).strip()
            if new_grp.lower() != str(prod["subject_group"]).strip().lower():
                changes.append(f"Tổ bộ môn: {prod['subject_group']} -> {new_grp}")
                
            # 2. Gender
            new_fem = parse_bool(row["Nữ"])
            prod_fem = bool(prod["is_female"])
            if new_fem != prod_fem:
                changes.append(f"Nữ: {prod_fem} -> {new_fem}")
                
            # 3. Employment type
            new_emp = str(row["Loại hợp đồng"]).strip().upper()
            prod_emp = str(prod["employment_type"]).strip().upper()
            if new_emp != prod_emp:
                changes.append(f"Loại hợp đồng: {prod_emp} -> {new_emp}")
                
            # 4. Guest rank
            new_gr = str(row["Học hàm học vị"]).strip() if not pd.isna(row["Học hàm học vị"]) else ""
            prod_gr = str(prod["guest_rank"] or "").strip()
            if new_gr.lower() != prod_gr.lower():
                changes.append(f"Học hàm học vị: {prod_gr} -> {new_gr}")
                
            # 5. Role
            new_role = str(row["Chức vụ"]).strip() if not pd.isna(row["Chức vụ"]) else ""
            prod_role = str(prod["role"] or "").strip()
            if new_role.lower() != prod_role.lower():
                changes.append(f"Chức vụ: {prod_role} -> {new_role}")
                
            # 6. Title
            new_title = str(row["Chức danh"]).strip() if not pd.isna(row["Chức danh"]) else ""
            prod_title = str(prod["title"] or "").strip()
            if new_title.lower() != prod_title.lower():
                changes.append(f"Chức danh: {prod_title} -> {new_title}")
                
            # 7. Police Rank
            new_pr = str(row["Cấp bậc quân hàm"]).strip() if not pd.isna(row["Cấp bậc quân hàm"]) else ""
            prod_pr = str(prod["police_rank"] or "").strip()
            if new_pr.lower() != prod_pr.lower():
                changes.append(f"Cấp bậc: {prod_pr} -> {new_pr}")

            if changes:
                df.at[idx, "diff_marker"] = "UPDATE"
                df.at[idx, "diff_detail"] = "; ".join(changes)
            else:
                df.at[idx, "diff_marker"] = "SKIP"
                df.at[idx, "diff_detail"] = "Không thay đổi"
        else:
            df.at[idx, "diff_marker"] = "NEW"
            df.at[idx, "diff_detail"] = "Cán bộ mới"
            
    return df


def diff_activities(df: pd.DataFrame, conn, timeframe_name: str) -> pd.DataFrame:
    """
    Compares activity logs with production.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.teacher_id, act.name as activity_type_name, a.log_date, a.quantity
        FROM activities a
        JOIN activity_types act ON a.activity_type_id = act.id
        JOIN timeframes tf ON a.timeframe_id = tf.id
        WHERE tf.name = ?
    """, (timeframe_name,))
    prod_rows = cursor.fetchall()
    prod_set = set()
    for r in prod_rows:
        key = (
            str(r["teacher_id"]),
            str(r["activity_type_name"]).strip().lower(),
            str(r["log_date"]).strip(),
            float(r["quantity"])
        )
        prod_set.add(key)

    df["diff_marker"] = "NEW"
    df["diff_detail"] = ""

    for idx, row in df.iterrows():
        try:
            t_id = str(int(float(str(row["Mã GV"]).strip())))
        except Exception:
            t_id = ""
            
        act_name = str(row["Tên loại hoạt động"]).strip().lower()
        try:
            log_date = pd.to_datetime(row["Ngày thực hiện"]).strftime("%Y-%m-%d")
        except Exception:
            log_date = ""
            
        qty_val = safe_float(row["Số lượng"])
        qty = float(qty_val) if qty_val is not None else 0.0

        key = (t_id, act_name, log_date, qty)
        if key in prod_set:
            df.at[idx, "diff_marker"] = "SKIP"
            df.at[idx, "diff_detail"] = "Đã tồn tại trong hệ thống"
        else:
            df.at[idx, "diff_marker"] = "NEW"
            df.at[idx, "diff_detail"] = "Hoạt động mới"

    return df


def diff_schedule(df: pd.DataFrame, conn, timeframe_id) -> pd.DataFrame:
    """
    Compares incoming schedule assignments with current production bulk teaching assignments.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.teacher_id, b.subject_name, b.loai, b.nhom, b.si_so, b.tiet_quy_doi, b.he_so_tin_chi
        FROM bulk_teaching_assignments b
        WHERE b.timeframe_id = ?
    """, (timeframe_id,))
    prod_rows = [dict(r) for r in cursor.fetchall()]
    
    # Map by teacher_id + subject_name + loai + nhom
    prod_map = {}
    for r in prod_rows:
        key = (
            int(r["teacher_id"]),
            str(r["subject_name"]).strip().lower(),
            str(r["loai"]).strip().upper(),
            str(r["nhom"] or "").strip().lower()
        )
        prod_map[key] = r

    df["diff_marker"] = "NEW"
    df["diff_detail"] = ""

    for idx, row in df.iterrows():
        t_id = int(float(row["Mã GV (Khóa)"]))
        sub = str(row["Tên môn học"]).strip()
        loai = str(row["Loại"]).strip().upper()
        nhom = str(row["Nhóm"] or "").strip()
        
        key = (t_id, sub.lower(), loai, nhom.lower())
        
        if key in prod_map:
            prod = prod_map[key]
            changes = []
            
            new_siso = int(safe_float(row["Sỉ số"]))
            prod_siso = int(prod["si_so"])
            if new_siso != prod_siso:
                changes.append(f"Sỉ số: {prod_siso} -> {new_siso}")
                
            new_tqd = float(safe_float(row["Tiết quy đổi"]))
            prod_tqd = float(prod["tiet_quy_doi"])
            if abs(new_tqd - prod_tqd) > 0.001:
                changes.append(f"Tiết QĐ: {prod_tqd} -> {new_tqd}")
                
            new_hstc = float(safe_float(row["Hệ số tín chỉ"]))
            prod_hstc = float(prod["he_so_tin_chi"])
            if abs(new_hstc - prod_hstc) > 0.001:
                changes.append(f"Hệ số TC: {prod_hstc} -> {new_hstc}")
                
            if changes:
                df.at[idx, "diff_marker"] = "UPDATE"
                df.at[idx, "diff_detail"] = "; ".join(changes)
            else:
                df.at[idx, "diff_marker"] = "SKIP"
                df.at[idx, "diff_detail"] = "Lớp học đã khớp"
        else:
            df.at[idx, "diff_marker"] = "NEW"
            df.at[idx, "diff_detail"] = "Lớp/môn mới"
            
    return df


def diff_aggregate_totals(df: pd.DataFrame, conn, timeframe_name: str) -> pd.DataFrame:
    """
    Compares aggregate totals override data with existing teacher_calculated_totals records.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM timeframes WHERE name = ?", (timeframe_name,))
    tf_row = cursor.fetchone()
    if not tf_row:
        df["diff_marker"] = "NEW"
        df["diff_detail"] = "Không tìm thấy năm học"
        return df
    tf_id = tf_row["id"]

    cursor.execute("""
        SELECT teacher_id, tong_gc_da_thuc_hien, nckh_da_thuc_hien, so_gio_duoc_mien_giam, dinh_muc_gc_phai_thuc_hien
        FROM teacher_calculated_totals
        WHERE timeframe_id = ? AND is_override = 1
    """, (tf_id,))
    exist_rows = cursor.fetchall()
    exist_map = {r["teacher_id"]: dict(r) for r in exist_rows}

    # Fetch teachers to match name/id
    cursor.execute("SELECT id, name FROM teachers")
    t_rows = cursor.fetchall()
    t_map_id = {str(row["id"]): row["id"] for row in t_rows}
    t_map_name = {row["name"].strip().lower(): row["id"] for row in t_rows}

    df["diff_marker"] = "NEW"
    df["diff_detail"] = ""

    for idx, row in df.iterrows():
        teacher_raw = str(row["Mã GV"]).strip()
        try:
            t_id_str = str(int(float(teacher_raw)))
        except ValueError:
            t_id_str = teacher_raw

        t_id = t_map_id.get(t_id_str)
        if not t_id:
            t_id = t_map_name.get(teacher_raw.lower())

        if not t_id:
            df.at[idx, "diff_marker"] = "NEW"
            df.at[idx, "diff_detail"] = f"Mã GV '{teacher_raw}' không tồn tại"
            continue

        if t_id in exist_map:
            exist = exist_map[t_id]
            changes = []

            new_gc = float(safe_float(row["Tổng GC thực hiện"]) or 0.0)
            exist_gc = float(exist["tong_gc_da_thuc_hien"] or 0.0)
            if abs(new_gc - exist_gc) > 0.001:
                changes.append(f"GC: {exist_gc} -> {new_gc}")

            new_nckh = float(safe_float(row["NCKH thực hiện"]) or 0.0)
            exist_nckh = float(exist["nckh_da_thuc_hien"] or 0.0)
            if abs(new_nckh - exist_nckh) > 0.001:
                changes.append(f"NCKH: {exist_nckh} -> {new_nckh}")

            new_miengiam = float(safe_float(row["Số giờ miễn giảm"]) or 0.0)
            exist_miengiam = float(exist["so_gio_duoc_mien_giam"] or 0.0)
            if abs(new_miengiam - exist_miengiam) > 0.001:
                changes.append(f"Miễn: {exist_miengiam} -> {new_miengiam}")

            new_dinhmuc = float(safe_float(row["Định mức GC"]) or 0.0)
            exist_dinhmuc = float(exist["dinh_muc_gc_phai_thuc_hien"] or 0.0)
            if abs(new_dinhmuc - exist_dinhmuc) > 0.001:
                changes.append(f"Định mức: {exist_dinhmuc} -> {new_dinhmuc}")

            if changes:
                df.at[idx, "diff_marker"] = "UPDATE"
                df.at[idx, "diff_detail"] = "; ".join(changes)
            else:
                df.at[idx, "diff_marker"] = "SKIP"
                df.at[idx, "diff_detail"] = "Ghi đè trùng khớp"
        else:
            df.at[idx, "diff_marker"] = "NEW"
            df.at[idx, "diff_detail"] = "Thiết lập ghi đè mới"

    return df
