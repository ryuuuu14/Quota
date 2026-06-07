import streamlit as st
import pandas as pd
import json
from datetime import datetime
from database import get_connection, init_db
from components import (
    render_sidebar,
    inject_premium_css,
    render_empty_state,
    render_warning_state,
)

init_db()

st.set_page_config(page_title="Phê duyệt Dữ liệu", page_icon="⚖️", layout="wide")
render_sidebar("pheduyet")
inject_premium_css()

# Ensure user is logged in as Admin
# Test compatibility: st.session_state.get("is_admin", False)
from auth import require_role
if not require_role(["admin"], page_title="⚖️ Phê duyệt Yêu cầu Nhập dữ liệu"):
    st.stop()

# If authenticated admin
col1, col2, col3 = st.columns([1, 10, 1])
with col2:
    st.markdown('<div style="margin-bottom: 24px;">', unsafe_allow_html=True)
    st.title("⚖️ Bảng Phê duyệt Yêu cầu Nhập dữ liệu")
    st.markdown("""
    <div style="font-size: 1.05rem; color: var(--md-on-surface-variant); margin-top: -8px; margin-bottom: 24px; line-height: 1.6;">
        Xem xét, đối chiếu và phê duyệt các lô dữ liệu tải lên từ các Đơn vị giảng dạy.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    conn = get_connection()
    batches_df = pd.read_sql_query("""
        SELECT * FROM import_batches 
        WHERE status = 'pending' 
        ORDER BY created_at DESC
    """, conn)
    
    if batches_df.empty:
        render_empty_state("Hiện không có yêu cầu phê duyệt nào đang chờ.")
        conn.close()
        st.stop()
        
    st.markdown("### 📋 Danh sách Yêu cầu đang chờ")
    
    # Let's list pending batches
    for idx, row in batches_df.iterrows():
        batch_id = int(row["id"])
        domain = row["domain"]
        dept_name = row["dept_name"] or "Quản trị viên"
        uploaded_by = row["uploaded_by"]
        filename = row["filename"]
        row_count = row["row_count"]
        created_at = row["created_at"]
        
        domain_label = {
            "teachers": "Hồ sơ Cán bộ",
            "activities": "Hoạt động miễn giảm/NCKH",
            "schedule": "Thời khóa biểu giảng dạy",
            "reduction_rules": "Yêu cầu quy tắc miễn giảm"
        }.get(domain, domain)
        
        with st.container():
            st.markdown(f"""
            <div class="md-card" style="padding: 16px 20px !important; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <span class="md-chip md-chip-primary" style="margin-right: 8px;">{domain_label}</span>
                        <strong>Lô #{batch_id}</strong> &nbsp;|&nbsp; Đơn vị: <strong>{dept_name}</strong>
                        <div style="font-size: 0.85rem; color: var(--md-on-surface-variant); margin-top: 4px;">
                            Người tải lên: {uploaded_by} &nbsp;•&nbsp; File: <code>{filename}</code> ({row_count} dòng) &nbsp;•&nbsp; Thời gian: {created_at}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Select batch button using native streamlit buttons placed carefully
            if st.button(f"🔍 Xem chi tiết Lô #{batch_id}", key=f"btn_view_{batch_id}"):
                st.session_state["selected_batch_id"] = batch_id
                st.rerun()

    # Detail section
    selected_batch_id = st.session_state.get("selected_batch_id")
    if selected_batch_id:
        # Check if still pending
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM import_batches WHERE id = ?", (selected_batch_id,))
        batch = cursor.fetchone()
        if not batch or batch["status"] != "pending":
            st.session_state["selected_batch_id"] = None
            st.rerun()
            
        st.markdown("---")
        st.markdown(f"## 🔎 Chi tiết Lô dữ liệu #{selected_batch_id}")
        
        domain = batch["domain"]
        dept_name = batch["dept_name"]

        # Load staging rows or parse rules
        if domain == "reduction_rules":
            diff_data = json.loads(batch["diff_json"]) if batch["diff_json"] else {}
            action = diff_data.get("action", "")
            rule_id = diff_data.get("id")
            name = diff_data.get("name", "")
            rule_type = diff_data.get("rule_type", "")
            teaching_pct = diff_data.get("teaching_reduction_pct", 0.0)
            nckh_pct = diff_data.get("nckh_reduction_pct", 0.0)
            
            action_label = {"create": "Thêm mới", "update": "Cập nhật/Sửa", "delete": "Xóa"}.get(action, action)
            type_label = {"ROLE": "Chức vụ Quản lý", "SPECIAL": "Diện miễn giảm khác"}.get(rule_type, rule_type)
            
            st.markdown(f"#### Chi tiết yêu cầu: **{action_label}**")
            st.markdown(f"""
            - **Tên quy tắc**: `{name}`
            - **Phân loại**: {type_label}
            - **Tỷ lệ miễn Giảng dạy**: `{teaching_pct}%`
            - **Tỷ lệ miễn NCKH**: `{nckh_pct}%`
            """)
            
            # Approve/Reject actions
            st.markdown("### ✍️ Quyết định phê duyệt")
            rejection_reason = st.text_input("Lý do từ chối (bắt buộc nếu từ chối):", key="rejection_reason_input")
            
            col_act1, col_act2 = st.columns(2)
            
            if col_act1.button("✅ Phê duyệt & Đưa vào hệ thống", type="primary", key="btn_approve_batch"):
                cursor = conn.cursor()
                try:
                    cursor.execute("BEGIN TRANSACTION")
                    decided_by = st.session_state["admin_username"]
                    now_str = datetime.now().isoformat()
                    
                    if action == "create":
                        cursor.execute("""
                            INSERT INTO reduction_rules (name, rule_type, teaching_reduction_pct, nckh_reduction_pct)
                            VALUES (?, ?, ?, ?)
                        """, (name, rule_type, teaching_pct, nckh_pct))
                    elif action == "update":
                        cursor.execute("""
                            UPDATE reduction_rules
                            SET name = ?, teaching_reduction_pct = ?, nckh_reduction_pct = ?
                            WHERE id = ?
                        """, (name, teaching_pct, nckh_pct, rule_id))
                    elif action == "delete":
                        cursor.execute("DELETE FROM reduction_rules WHERE id = ?", (rule_id,))
                        
                    # Update batch status
                    cursor.execute("""
                        UPDATE import_batches 
                        SET status = 'approved', decided_at = ?, decided_by = ?
                        WHERE id = ?
                    """, (now_str, decided_by, selected_batch_id))
                    
                    cursor.execute("COMMIT")
                    st.success("✅ Đã phê duyệt và cập nhật dữ liệu thành công!")
                    st.session_state["selected_batch_id"] = None
                    st.rerun()
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    st.error(f"Lỗi khi phê duyệt: {str(e)}")
            
            if col_act2.button("❌ Từ chối yêu cầu", key="btn_reject_batch"):
                if not rejection_reason.strip():
                    st.error("Vui lòng nhập lý do từ chối.")
                else:
                    cursor = conn.cursor()
                    try:
                        decided_by = st.session_state["admin_username"]
                        now_str = datetime.now().isoformat()
                        
                        cursor.execute("""
                            UPDATE import_batches 
                            SET status = 'rejected', rejection_reason = ?, decided_at = ?, decided_by = ?
                            WHERE id = ?
                        """, (rejection_reason, now_str, decided_by, selected_batch_id))
                        
                        conn.commit()
                        st.success("❌ Đã từ chối lô dữ liệu và phản hồi lại Đơn vị.")
                        st.session_state["selected_batch_id"] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi từ chối: {str(e)}")
        else:
            staging_table = f"staging_{domain}"
            staging_df = pd.read_sql_query(f"""
                SELECT * FROM {staging_table} 
                WHERE batch_id = ?
                ORDER BY row_num ASC
            """, conn, params=(selected_batch_id,))
            
            if staging_df.empty:
                st.info("Lô dữ liệu trống hoặc không có dòng hợp lệ.")
            else:
                # Let's count markers
                marker_counts = staging_df["diff_marker"].value_counts().to_dict()
                new_c = marker_counts.get("NEW", 0)
                upd_c = marker_counts.get("UPDATE", 0)
                skip_c = marker_counts.get("SKIP", 0)
                
                st.markdown(f"""
                <div style="display: flex; gap: 16px; margin-bottom: 16px;">
                    <span class="md-chip md-chip-green">Mới: {new_c}</span>
                    <span class="md-chip md-chip-amber">Cập nhật: {upd_c}</span>
                    <span class="md-chip" style="background-color: var(--md-surface-container-high);">Bỏ qua: {skip_c}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Render color-coded dataframe
                # Map column names to friendly headers based on domain
                if domain == "teachers":
                    display_cols = ["row_num", "teacher_id", "teacher_name", "department", "title", "role", "employment_type", "subject_group", "diff_marker", "diff_detail"]
                    display_rename = {
                        "row_num": "Dòng", "teacher_id": "Mã GV", "teacher_name": "Họ tên", "department": "Đơn vị", "title": "Chức danh",
                        "role": "Chức vụ", "employment_type": "Loại HĐ", "subject_group": "Tổ môn",
                        "diff_marker": "Trạng thái", "diff_detail": "Chi tiết thay đổi"
                    }
                elif domain == "activities":
                    display_cols = ["row_num", "teacher_name", "activity_type_name", "log_date", "quantity", "timeframe_name", "diff_marker", "diff_detail"]
                    display_rename = {
                        "row_num": "Dòng", "teacher_name": "Mã GV", "activity_type_name": "Hoạt động", "log_date": "Ngày",
                        "quantity": "Số lượng", "timeframe_name": "Năm học", "diff_marker": "Trạng thái", "diff_detail": "Chi tiết thay đổi"
                    }
                elif domain == "aggregate_totals":
                    display_cols = ["row_num", "teacher_name", "tong_gc_da_thuc_hien", "nckh_da_thuc_hien", "so_gio_duoc_mien_giam", "dinh_muc_gc_phai_thuc_hien", "timeframe_name", "diff_marker", "diff_detail"]
                    display_rename = {
                        "row_num": "Dòng", "teacher_name": "Mã GV", "tong_gc_da_thuc_hien": "Tổng GC thực hiện", "nckh_da_thuc_hien": "NCKH thực hiện",
                        "so_gio_duoc_mien_giam": "Miễn giảm", "dinh_muc_gc_phai_thuc_hien": "Định mức GC", "timeframe_name": "Năm học",
                        "diff_marker": "Trạng thái", "diff_detail": "Chi tiết thay đổi"
                    }
                else: # schedule
                    display_cols = ["row_num", "teacher_name", "subject_name", "loai", "nhom", "si_so", "tiet_quy_doi", "he_so_tin_chi", "diff_marker", "diff_detail"]
                    display_rename = {
                        "row_num": "Dòng", "teacher_name": "Họ tên", "subject_name": "Tên môn", "loai": "Loại",
                        "nhom": "Nhóm", "si_so": "Sỉ số", "tiet_quy_doi": "Tiết QĐ", "he_so_tin_chi": "HS TC",
                        "diff_marker": "Trạng thái", "diff_detail": "Chi tiết thay đổi"
                    }
                    
                sub_df = staging_df[display_cols].rename(columns=display_rename)
                st.dataframe(sub_df, use_container_width=True, hide_index=True)
                
                # Approve/Reject actions
                st.markdown("### ✍️ Quyết định phê duyệt")
                
                rejection_reason = st.text_input("Lý do từ chối (bắt buộc nếu từ chối):", key="rejection_reason_input")
                
                col_act1, col_act2 = st.columns(2)
                
                if col_act1.button("✅ Phê duyệt & Đưa vào hệ thống", type="primary", key="btn_approve_batch"):
                    cursor = conn.cursor()
                    try:
                        cursor.execute("BEGIN TRANSACTION")
                        
                        decided_by = st.session_state["admin_username"]
                        now_str = datetime.now().isoformat()
                        
                        # Core commit logic per domain
                        if domain == "teachers":
                            for _, r in staging_df.iterrows():
                                marker = r["diff_marker"]
                                if marker == "NEW":
                                    # 1. Insert teacher
                                    cursor.execute("""
                                        INSERT INTO teachers (name, subject_group, is_female, employment_type, guest_rank, total_12m_salary, police_rank_id, salary_coefficient)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (r["teacher_name"], r["subject_group"], r["is_female"], r["employment_type"], r["guest_rank"], r["total_12m_salary"], r["police_rank_id"], r["salary_coefficient"]))
                                    new_id = cursor.lastrowid
                                    
                                    # 2. Insert role history for Title & Dept
                                    cursor.execute("""
                                        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
                                        VALUES (?, 'TITLE', ?, ?)
                                    """, (new_id, r["title"], now_str[:10]))
                                    cursor.execute("""
                                        INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
                                        VALUES (?, 'DEPARTMENT', ?, ?)
                                    """, (new_id, r["department"], now_str[:10]))
                                    if r.get("role"):
                                        cursor.execute("""
                                            INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date)
                                            VALUES (?, 'ROLE', ?, ?)
                                        """, (new_id, r["role"], now_str[:10]))
    
                                    
                                elif marker == "UPDATE":
                                    # Find existing teacher by ID if available, else by name + department
                                    t_id = r.get("teacher_id")
                                    if pd.isna(t_id): t_id = None
                                    
                                    if t_id:
                                        cursor.execute("""
                                            SELECT t.id, 
                                                   (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'TITLE' ORDER BY start_date DESC LIMIT 1) as title,
                                                   (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'DEPARTMENT' ORDER BY start_date DESC LIMIT 1) as dept,
                                                   (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'ROLE' ORDER BY start_date DESC LIMIT 1) as role
                                            FROM teachers t WHERE t.id = ?
                                        """, (t_id,))
                                    else:
                                        cursor.execute("""
                                            SELECT t.id, 
                                                   (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'TITLE' ORDER BY start_date DESC LIMIT 1) as title,
                                                   (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'DEPARTMENT' ORDER BY start_date DESC LIMIT 1) as dept,
                                                   (SELECT value_text FROM teacher_role_history WHERE teacher_id = t.id AND record_type = 'ROLE' ORDER BY start_date DESC LIMIT 1) as role
                                            FROM teachers t WHERE t.name = ?
                                        """, (r["teacher_name"],))
                                    gvs = cursor.fetchall()
                                    old_title = None
                                    old_dept = None
                                    old_role = None
                                    
                                    if not t_id:
                                        for gv in gvs:
                                            if str(gv["dept"]).strip().lower() == str(r["department"]).strip().lower():
                                                t_id = gv["id"]
                                                old_title = gv["title"]
                                                old_dept = gv["dept"]
                                                old_role = gv["role"]
                                                break
                                    elif gvs:
                                        old_title = gvs[0]["title"]
                                        old_dept = gvs[0]["dept"]
                                        old_role = gvs[0]["role"]
                                    
                                    if t_id:
                                        # Update basic details
                                        cursor.execute("""
                                            UPDATE teachers 
                                            SET subject_group = ?, is_female = ?, employment_type = ?, guest_rank = ?
                                            WHERE id = ?
                                        """, (r["subject_group"], r["is_female"], r["employment_type"], r["guest_rank"], t_id))
                                        
                                        # If title changed, update role history
                                        if r["title"] and r["title"] != old_title:
                                            cursor.execute("UPDATE teacher_role_history SET end_date = date(?, '-1 day') WHERE teacher_id = ? AND record_type = 'TITLE' AND end_date IS NULL", (now_str[:10], t_id))
                                            cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (?, 'TITLE', ?, ?)", (t_id, r["title"], now_str[:10]))
                                        
                                        # If department changed, update role history
                                        if r["department"] and r["department"] != old_dept:
                                            cursor.execute("UPDATE teacher_role_history SET end_date = date(?, '-1 day') WHERE teacher_id = ? AND record_type = 'DEPARTMENT' AND end_date IS NULL", (now_str[:10], t_id))
                                            cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (?, 'DEPARTMENT', ?, ?)", (t_id, r["department"], now_str[:10]))
                                            
                                        # If role changed, update role history
                                        if r.get("role") and r["role"] != old_role:
                                            cursor.execute("UPDATE teacher_role_history SET end_date = date(?, '-1 day') WHERE teacher_id = ? AND record_type = 'ROLE' AND end_date IS NULL", (now_str[:10], t_id))
                                            cursor.execute("INSERT INTO teacher_role_history (teacher_id, record_type, value_text, start_date) VALUES (?, 'ROLE', ?, ?)", (t_id, r["role"], now_str[:10]))
    
                                elif marker == "DELETE":
                                    t_id = r.get("teacher_id")
                                    if pd.isna(t_id): t_id = None
                                    if t_id:
                                        cursor.execute("DELETE FROM session_teacher_totals WHERE teacher_id = ?", (t_id,))
                                        cursor.execute("DELETE FROM activity_logs WHERE teacher_id = ?", (t_id,))
                                        cursor.execute("DELETE FROM teacher_role_history WHERE teacher_id = ?", (t_id,))
                                        cursor.execute("DELETE FROM teacher_rank_history WHERE teacher_id = ?", (t_id,))
                                        cursor.execute("DELETE FROM manual_conversions WHERE teacher_id = ?", (t_id,))
                                        cursor.execute("DELETE FROM payroll_records WHERE teacher_id = ?", (t_id,))
                                        cursor.execute("DELETE FROM teachers WHERE id = ?", (t_id,))
    
                        elif domain == "activities":
                            # Lookup timeframe & teacher cache
                            cursor.execute("SELECT id, name FROM timeframes")
                            tf_map = {row["name"].strip().lower(): row["id"] for row in cursor.fetchall()}
                            cursor.execute("SELECT id, name FROM teachers")
                            t_map = {row["name"].strip().lower(): row["id"] for row in cursor.fetchall()}
                            
                            # Lookup activity types cache
                            cursor.execute("SELECT * FROM activity_types")
                            act_types_list = cursor.fetchall()
                            act_map = {row["name"].strip().lower(): row["id"] for row in act_types_list}
                            
                            for _, r in staging_df.iterrows():
                                if r["diff_marker"] == "NEW":
                                    try:
                                        t_id = int(float(str(r["teacher_name"]).strip()))
                                    except Exception:
                                        t_id = None
                                    tf_id = tf_map.get(str(r["timeframe_name"]).strip().lower())
                                    act_name_lower = str(r["activity_type_name"]).strip().lower()
                                    
                                    if act_name_lower not in act_map:
                                        # Insert new activity type if missing
                                        cursor.execute("INSERT INTO activity_types (name, category, unit, base_conversion_rate) VALUES (?, 'Khác', 'Giờ', 1.0)", (r["activity_type_name"],))
                                        act_id = cursor.lastrowid
                                        act_map[act_name_lower] = act_id
                                    else:
                                        act_id = act_map[act_name_lower]
                                        
                                    if t_id and tf_id:
                                        # Fetch activity type details for conversion rate calculation
                                        cursor.execute("SELECT * FROM activity_types WHERE id = ?", (act_id,))
                                        act_row = cursor.fetchone()
                                        
                                        log_row_dict = {
                                            "quantity": r["quantity"],
                                            "class_level": r["class_level"],
                                            "class_type": r["class_type"],
                                            "student_count": r["student_count"],
                                            "nckh_level": r["nckh_level"],
                                            "is_main_author": r["is_main_author"],
                                            "is_foreign_language_instruction": r["is_foreign_language_instruction"]
                                        }
                                        from calculations import calculate_activity_hours
                                        conv_hours = calculate_activity_hours(log_row_dict, dict(act_row))
                                        
                                        cursor.execute("""
                                            INSERT INTO activity_logs (teacher_id, activity_type_id, log_date, quantity, class_level, class_type, student_count, nckh_level, is_main_author, is_foreign_language_instruction, note, timeframe_id, converted_hours)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (t_id, act_id, r["log_date"], r["quantity"], r["class_level"], r["class_type"], r["student_count"], r["nckh_level"], r["is_main_author"], r["is_foreign_language_instruction"], r["note"], tf_id, conv_hours))
    
                        elif domain == "schedule":
                            # Timeframe mapping
                            cursor.execute("SELECT id, name FROM timeframes")
                            tf_map = {row["name"].strip().lower(): row["id"] for row in cursor.fetchall()}
                            cursor.execute("SELECT id, name FROM teachers")
                            t_map = {row["name"].strip().lower(): row["id"] for row in cursor.fetchall()}
                            
                            for _, r in staging_df.iterrows():
                                marker = r["diff_marker"]
                                tf_id = tf_map.get(str(r["timeframe_name"]).strip().lower())
                                t_id = t_map.get(str(r["teacher_name"]).strip().lower())
                                
                                if not t_id:
                                    continue
                                    
                                if marker == "NEW":
                                    cursor.execute("""
                                        INSERT INTO bulk_teaching_assignments (timeframe_id, teacher_id, subject_name, loai, nhom, si_so, tiet_quy_doi, he_so_tin_chi, ghi_chu, he_so_lop_dong, tiet_thuc_day)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (tf_id, t_id, r["subject_name"], r["loai"], r["nhom"], r["si_so"], r["tiet_quy_doi"], r["he_so_tin_chi"], r["validation_errors"], r["he_so_lop_dong"] or 1.0, r["tiet_thuc_day"] or 0.0))
                                elif marker == "UPDATE":
                                    cursor.execute("""
                                        UPDATE bulk_teaching_assignments
                                        SET si_so = ?, tiet_quy_doi = ?, he_so_tin_chi = ?, he_so_lop_dong = ?, tiet_thuc_day = ?
                                        WHERE timeframe_id = ? AND teacher_id = ? AND subject_name = ? AND loai = ? AND nhom = ?
                                    """, (r["si_so"], r["tiet_quy_doi"], r["he_so_tin_chi"], r["he_so_lop_dong"] or 1.0, r["tiet_thuc_day"] or 0.0, tf_id, t_id, r["subject_name"], r["loai"], r["nhom"]))
    
                        elif domain == "aggregate_totals":
                            # Timeframe mapping
                            cursor.execute("SELECT id, name FROM timeframes")
                            tf_map = {row["name"].strip().lower(): row["id"] for row in cursor.fetchall()}
                            
                            # Teacher mapping
                            cursor.execute("SELECT id, name FROM teachers")
                            t_rows = cursor.fetchall()
                            t_map_id = {str(row["id"]): row["id"] for row in t_rows}
                            t_map_name = {row["name"].strip().lower(): row["id"] for row in t_rows}
                            
                            for _, r in staging_df.iterrows():
                                tf_id = tf_map.get(str(r["timeframe_name"]).strip().lower())
                                teacher_raw = str(r["teacher_name"]).strip()
                                
                                t_id = t_map_id.get(teacher_raw)
                                if not t_id:
                                    t_id = t_map_name.get(teacher_raw.lower())
                                    
                                if not t_id or not tf_id:
                                    continue
                                
                                cursor.execute("""
                                    INSERT INTO teacher_calculated_totals (
                                        timeframe_id, teacher_id, tong_gc_da_thuc_hien, nckh_da_thuc_hien, so_gio_duoc_mien_giam, dinh_muc_gc_phai_thuc_hien, is_override
                                    ) VALUES (?, ?, ?, ?, ?, ?, 1)
                                    ON CONFLICT(timeframe_id, teacher_id) DO UPDATE SET
                                        tong_gc_da_thuc_hien=excluded.tong_gc_da_thuc_hien,
                                        nckh_da_thuc_hien=excluded.nckh_da_thuc_hien,
                                        so_gio_duoc_mien_giam=excluded.so_gio_duoc_mien_giam,
                                        dinh_muc_gc_phai_thuc_hien=excluded.dinh_muc_gc_phai_thuc_hien,
                                        is_override=1
                                """, (
                                    tf_id, t_id,
                                    r["tong_gc_da_thuc_hien"],
                                    r["nckh_da_thuc_hien"],
                                    r["so_gio_duoc_mien_giam"],
                                    r["dinh_muc_gc_phai_thuc_hien"]
                                ))

                        # Update batch status
                        cursor.execute("""
                            UPDATE import_batches 
                            SET status = 'approved', decided_at = ?, decided_by = ?
                            WHERE id = ?
                        """, (now_str, decided_by, selected_batch_id))
                        
                        # Delete staging rows
                        cursor.execute(f"DELETE FROM {staging_table} WHERE batch_id = ?", (selected_batch_id,))
                        
                        cursor.execute("COMMIT")
                        st.success("✅ Đã phê duyệt và cập nhật dữ liệu thành công!")
                        st.session_state["selected_batch_id"] = None
                        st.rerun()
                    except Exception as e:
                        cursor.execute("ROLLBACK")
                        st.error(f"Lỗi khi phê duyệt: {str(e)}")
    
                if col_act2.button("❌ Từ chối yêu cầu", key="btn_reject_batch"):
                    if not rejection_reason.strip():
                        st.error("Vui lòng nhập lý do từ chối.")
                    else:
                        cursor = conn.cursor()
                        try:
                            decided_by = st.session_state["admin_username"]
                            now_str = datetime.now().isoformat()
                            
                            cursor.execute("""
                                UPDATE import_batches 
                                SET status = 'rejected', rejection_reason = ?, decided_at = ?, decided_by = ?
                                WHERE id = ?
                            """, (rejection_reason, now_str, decided_by, selected_batch_id))
                            
                            # Delete staging rows
                            cursor.execute(f"DELETE FROM {staging_table} WHERE batch_id = ?", (selected_batch_id,))
                            
                            conn.commit()
                            st.success("❌ Đã từ chối lô dữ liệu và phản hồi lại Đơn vị.")
                            st.session_state["selected_batch_id"] = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi khi từ chối: {str(e)}")
    conn.close()
