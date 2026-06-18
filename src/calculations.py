import pandas as pd
import streamlit as st
from database import get_connection


def calculate_t04_weeks(start_date, end_date, holidays=None):
    """
    Tính số tuần theo quy định T04 (Điều 10.1.b):
    - 5 ngày làm việc = 1 tuần.
    - Chỉ đếm ngày làm việc (Thứ 2 - Thứ 6), bỏ Thứ 7, Chủ nhật.
    - Nếu còn dư ngày -> tính tỉ lệ (số ngày / 5).
    - Loại bỏ các ngày trùng với danh sách ngày nghỉ (holidays).
    """
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    if start_date > end_date:
        return 0.0
        
    days_range = pd.date_range(start=start_date, end=end_date)
    
    active_days = 0
    for day in days_range:
        if day.weekday() >= 5:
            continue
        is_holiday = False
        if holidays is not None:
            for h_start, h_end in holidays:
                if h_start <= day <= h_end:
                    is_holiday = True
                    break
        if not is_holiday:
            active_days += 1
            
    if active_days <= 0:
        return 0.0
    full_weeks = active_days // 5
    rem = active_days % 5
    return float(full_weeks + rem / 5.0)



@st.cache_data(ttl=300)
def get_timeframe_dates(timeframe_id=None):
    conn = get_connection()
    tf_query = "SELECT * FROM timeframes"
    tf_params = []
    if timeframe_id is not None:
        tf_query += " WHERE id = ?"
        tf_params.append(int(timeframe_id))
    else:
        tf_query += " ORDER BY start_date DESC LIMIT 1"
        
    tf_df = pd.read_sql_query(tf_query, conn, params=tf_params)
    conn.close()
    if tf_df.empty:
        return None, None, None, None
        
    start_date = pd.to_datetime(tf_df.iloc[0]['start_date'])
    end_date = pd.to_datetime(tf_df.iloc[0]['end_date'])
    std_weeks = float(tf_df.iloc[0].get('standard_academic_weeks', 44.0))
    return int(tf_df.iloc[0]['id']), start_date, end_date, std_weeks

def get_timeframe_gap_dates(start_date, end_date):
    """
    Return (gap_start, gap_end) representing the period between the end_date 
    and the end of a full 52-week calendar year from start_date.
    Returns (None, None) if there is no gap (timeframe is >= 52 weeks).
    """
    s_dt = pd.to_datetime(start_date)
    e_dt = pd.to_datetime(end_date)
    full_year_end = s_dt + pd.Timedelta(weeks=52) - pd.Timedelta(days=1)
    
    if e_dt >= full_year_end:
        return None, None
        
    gap_start = e_dt + pd.Timedelta(days=1)
    gap_end = full_year_end
    return gap_start, gap_end


def calculate_activity_hours(log_row, activity_type_row):
    """
    Tính toán quy đổi giờ chuẩn cho từng hoạt động theo quy định T04 (Điều 8)
    """
    base = float(log_row['quantity']) * float(activity_type_row['base_conversion_rate'])
    
    if activity_type_row['category'] == 'Giảng dạy':
        if not activity_type_row['is_teaching_activity']:
            return base

        multiplier = 1.0
        # Đào tạo trình độ Đại học
        if log_row['class_level'] == 'Đại học':
            if log_row['class_type'] in ['Lý thuyết', 'Thảo luận', 'Bài tập', 'Xêmina']:
                if 41 <= log_row['student_count'] <= 60: multiplier = 1.2
                elif 61 <= log_row['student_count'] <= 80: multiplier = 1.4
                elif log_row['student_count'] > 80: multiplier = 1.5
            elif log_row['class_type'] in ['Ngoại ngữ/CNTT', 'Kỹ thuật hình sự']:
                if 26 <= log_row['student_count'] <= 40: multiplier = 1.2
                elif 41 <= log_row['student_count'] <= 60: multiplier = 1.4
                elif log_row['student_count'] > 60: multiplier = 1.5
            elif log_row['class_type'] == 'Thực hành':
                if 41 <= log_row['student_count'] <= 55: multiplier = 1.2
                elif 56 <= log_row['student_count'] <= 70: multiplier = 1.4
                elif log_row['student_count'] > 70: multiplier = 1.5

        # Đào tạo Thạc sĩ
        elif log_row['class_level'] == 'Thạc sĩ':
            if log_row['student_count'] <= 50: multiplier = 1.3
            else: multiplier = 1.5

        # Đào tạo Tiến sĩ
        elif log_row['class_level'] == 'Tiến sĩ':
            multiplier = 2.0

        # Trung cấp LLCT
        elif log_row['class_level'] == 'LLCT Trung cấp':
            if log_row['student_count'] <= 50: multiplier = 1.0
            else: multiplier = 1.2

        # Cao cấp LLCT
        elif log_row['class_level'] == 'LLCT Cao cấp':
            if log_row['student_count'] <= 50: multiplier = 1.3
            else: multiplier = 1.5

        # Bồi dưỡng (Điều 8.1.e): rate đã được lưu đúng trong DB (1.0/1.3/1.5/2.0)
        # Không nhân hệ số số học viên — chỉ dùng base (quantity * db_rate)
        elif log_row['class_level'] == 'Bồi dưỡng':
            return base  # multiplier stays 1.0, DB rate encodes the coefficient

        if log_row.get('is_foreign_language_instruction'):
            if log_row['student_count'] <= 40:
                multiplier = 1.5
            elif log_row['student_count'] <= 60:
                multiplier = 1.7
            else:
                multiplier = 2.0

        return base * multiplier

    # Bồi dưỡng category (activity_type.category == 'Bồi dưỡng')
    elif activity_type_row['category'] == 'Bồi dưỡng':
        return base  # rate already encoded in DB per Điều 8.1.e

    elif activity_type_row['category'] == 'NCKH':
        return base

    else:
        return base

def _generate_timeline_segments(tf_start, tf_end, title_recs, dept_recs, role_recs, rules_dict):
    """
    Tạo các đoạn thời gian (segments) dựa trên thay đổi về chức danh, khoa/phòng, nhiệm vụ kiêm nhiệm,
    và các mốc thời gian đặc biệt của Trợ giảng (12 và 24 tháng).
    """
    dates = set()
    dates.add(pd.to_datetime(tf_start))
    dates.add(pd.to_datetime(tf_end) + pd.Timedelta(days=1))
    
    for r_list in [title_recs, dept_recs]:
        for _, r in r_list.iterrows():
            r_start = max(pd.to_datetime(tf_start), pd.to_datetime(r['start_date']))
            r_end = min(pd.to_datetime(tf_end), pd.to_datetime(r['end_date'])) if pd.notnull(r['end_date']) else pd.to_datetime(tf_end)
            if r_start <= r_end:
                dates.add(r_start)
                dates.add(r_end + pd.Timedelta(days=1))

    for _, r in role_recs.iterrows():
        rid = r['reduction_rule_id']
        if rid in rules_dict and rules_dict[rid]['rule_type'] == 'ROLE':
            r_start = max(pd.to_datetime(tf_start), pd.to_datetime(r['start_date']))
            r_end = min(pd.to_datetime(tf_end), pd.to_datetime(r['end_date'])) if pd.notnull(r['end_date']) else pd.to_datetime(tf_end)
            if r_start <= r_end:
                dates.add(r_start)
                dates.add(r_end + pd.Timedelta(days=1))
                
    # Add dynamic transition points for Trợ giảng reductions (months 12 and 24)
    for _, r in title_recs.iterrows():
        if r['value_text'] == 'Trợ giảng':
            app_date = pd.to_datetime(r['start_date'])
            t12 = app_date + pd.DateOffset(months=12)
            t24 = app_date + pd.DateOffset(months=24)
            for t in [t12, t24]:
                if pd.to_datetime(tf_start) <= t <= pd.to_datetime(tf_end):
                    dates.add(t)
                    
    sorted_dates = sorted(list(dates))
    segments = []
    for i in range(len(sorted_dates) - 1):
        seg_start = sorted_dates[i]
        seg_end = sorted_dates[i+1] - pd.Timedelta(days=1)
        if seg_start <= seg_end:
            segments.append((seg_start, seg_end))
            
    return segments


def _calculate_tro_giang_reductions(seg_start, seg_end, title_name, title_recs, seg_base_gc, role_t_red, holidays_list, std_weeks):
    """
    Tính số giờ chuẩn được giảm cho chức danh Trợ giảng (Điều 10.3.a).
    """
    reduced_gc = 0.0
    reductions_desc = []
    
    if title_name == 'Trợ giảng':
        tro_giang_rec = title_recs[title_recs['value_text'] == 'Trợ giảng'].iloc[0]
        appointment_date = pd.to_datetime(tro_giang_rec['start_date'])
        
        # 1st 12 months (exclusive end date)
        end_12m = appointment_date + pd.DateOffset(months=12)
        # Next 12 months (exclusive end date)
        end_24m = appointment_date + pd.DateOffset(months=24)
        
        # Check segment overlap with 1st 12 months: [appointment_date, end_12m - 1 day]
        p1_start = max(seg_start, appointment_date)
        p1_end = min(seg_end, end_12m - pd.Timedelta(days=1))
        if p1_start <= p1_end:
            p1_weeks = calculate_t04_weeks(p1_start, p1_end, holidays_list)
            red_gc = seg_base_gc * (1 - role_t_red / 100.0) * 0.5 * (p1_weeks / std_weeks)
            reduced_gc += red_gc
            reductions_desc.append(f"Trợ giảng 12 tháng đầu (giảm 50% x {p1_weeks:.1f} tuần)")
                
        # Check segment overlap with next 12 months: [end_12m, end_24m - 1 day]
        p2_start = max(seg_start, end_12m)
        p2_end = min(seg_end, end_24m - pd.Timedelta(days=1))
        if p2_start <= p2_end:
            p2_weeks = calculate_t04_weeks(p2_start, p2_end, holidays_list)
            red_gc = seg_base_gc * (1 - role_t_red / 100.0) * 0.2 * (p2_weeks / std_weeks)
            reduced_gc += red_gc
            reductions_desc.append(f"Trợ giảng tháng 13-24 (giảm 20% x {p2_weeks:.1f} tuần)")
            
    return reduced_gc, reductions_desc


def _calculate_point2_reductions(point2_leaves, seg_data, tf_start, tf_end, holidays_list):
    """
    Tính giảm trừ theo điểm (2) của quy định (giảm 100% định mức giảng dạy & các nhiệm vụ khác).
    Trả về (reduced_gc, reduced_nvk, max_flat_nckh_pct, reductions_desc).
    """
    reduced_gc = 0.0
    reduced_nvk = 0.0
    max_flat_nckh_pct = 0.0
    reductions_desc = []
    
    for r, rule in point2_leaves:
        nckh_pct = rule['nckh_reduction_pct']
        if nckh_pct > 0:
            r_start_full = pd.to_datetime(r['start_date'])
            r_end_full = pd.to_datetime(r['end_date'])
            if nckh_pct == 60.0:
                if r_start_full < pd.to_datetime(tf_start) or r_end_full > pd.to_datetime(tf_end):
                    nckh_pct = 30.0
            if nckh_pct > max_flat_nckh_pct:
                max_flat_nckh_pct = nckh_pct

    for seg in seg_data:
        seg_intervals = []
        for r, rule in point2_leaves:
            r_start = max(pd.to_datetime(tf_start), pd.to_datetime(r['start_date']))
            r_end_full = pd.to_datetime(r['end_date'])
            r_end = min(pd.to_datetime(tf_end), r_end_full)

            has_override = pd.notnull(r.get('actual_weeks_override')) and str(r.get('actual_weeks_override')).strip() != ''
            override_val = float(r['actual_weeks_override']) if has_override else None
            total_leaf_days = max(1, (r_end - r_start).days + 1) if has_override else 0

            inter_start = max(seg['start'], r_start)
            inter_end = min(seg['end'], r_end)
            if inter_start <= inter_end:
                seg_days = (inter_end - inter_start).days + 1
                seg_override = (override_val * (seg_days / total_leaf_days)) if has_override else None
                seg_intervals.append((inter_start, inter_end, rule, r_end_full, seg_override))
        if not seg_intervals:
            continue
        seg_intervals.sort(key=lambda x: x[0])
        merged = []
        cur_start, cur_end, cur_rule, cur_r_end_full, cur_override = seg_intervals[0]
        for s, e, rule, r_end_full, seg_override in seg_intervals[1:]:
            if s <= cur_end:
                cur_end = max(cur_end, e)
                cur_r_end_full = max(cur_r_end_full, r_end_full)
                if rule['nckh_reduction_pct'] > cur_rule['nckh_reduction_pct']:
                    cur_rule = rule
                    cur_override = seg_override if seg_override is not None else cur_override
            else:
                merged.append((cur_start, cur_end, cur_rule, cur_r_end_full, cur_override))
                cur_start, cur_end, cur_rule, cur_r_end_full, cur_override = s, e, rule, r_end_full, seg_override
        merged.append((cur_start, cur_end, cur_rule, cur_r_end_full, cur_override))

        for m_start, m_end, rule, m_r_end_full, m_override in merged:
            if m_override is not None:
                inter_weeks = m_override
            elif m_r_end_full > seg['end']:
                inter_weeks = min(calculate_t04_weeks(m_start, m_r_end_full, holidays_list), seg['weeks'])
            else:
                inter_weeks = calculate_t04_weeks(m_start, m_end, holidays_list)
            if seg['weeks'] > 0:
                red_gc = seg['req_gc'] * (inter_weeks / seg['weeks'])
                red_nvk = seg['req_nvk'] * (inter_weeks / seg['weeks'])
            else:
                red_gc = 0.0
                red_nvk = 0.0
            reduced_gc += red_gc
            reduced_nvk += red_nvk

    for r, rule in point2_leaves:
        desc = f"{rule['name']} ({rule['rule_type']})"
        reductions_desc.append(desc)

    return reduced_gc, reduced_nvk, max_flat_nckh_pct, reductions_desc


def _calculate_point3_reductions(point3_leaves, point2_leaves, seg_data, tf_start, tf_end, holidays_list):
    """
    Tính giảm trừ theo điểm (3) của quy định (giảm theo tỷ lệ % định mức giảng dạy & NCKH).
    Tránh trùng lặp với thời gian nghỉ điểm (2).
    Trả về (reduced_gc, reduced_nckh, reductions_desc).
    """
    reduced_gc = 0.0
    reduced_nckh = 0.0
    reductions_desc = []

    for seg in seg_data:
        seg_intervals = []
        for r, rule in point3_leaves:
            r_start = max(pd.to_datetime(tf_start), pd.to_datetime(r['start_date']))
            r_end = min(pd.to_datetime(tf_end), pd.to_datetime(r['end_date']))
            if r_start > r_end: continue

            has_override = pd.notnull(r.get('actual_weeks_override')) and str(r.get('actual_weeks_override')).strip() != ''
            override_val = float(r['actual_weeks_override']) if has_override else None
            total_leaf_days = max(1, (r_end - r_start).days + 1) if has_override else 0

            inter_start = max(seg['start'], r_start)
            inter_end = min(seg['end'], r_end)
            if inter_start <= inter_end:
                seg_days = (inter_end - inter_start).days + 1
                seg_override = (override_val * (seg_days / total_leaf_days)) if has_override else None
                seg_intervals.append((inter_start, inter_end, rule, r_end, seg_override))

        if not seg_intervals:
            continue

        seg_intervals.sort(key=lambda x: x[0])
        merged = []
        cur_start, cur_end, cur_rule, cur_r_end, cur_override = seg_intervals[0]
        for s, e, rule, r_end, seg_override in seg_intervals[1:]:
            if s <= cur_end:
                cur_end = max(cur_end, e)
                cur_r_end = max(cur_r_end, r_end)
                merged_rule = dict(cur_rule)
                merged_rule['teaching_reduction_pct'] = max(cur_rule['teaching_reduction_pct'], rule['teaching_reduction_pct'])
                merged_rule['nckh_reduction_pct'] = max(cur_rule['nckh_reduction_pct'], rule['nckh_reduction_pct'])
                cur_rule = merged_rule
                if cur_override is not None or seg_override is not None:
                    cur_override = max(cur_override or 0, seg_override or 0)
            else:
                merged.append((cur_start, cur_end, cur_rule, cur_r_end, cur_override))
                cur_start, cur_end, cur_rule, cur_r_end, cur_override = s, e, rule, r_end, seg_override
        merged.append((cur_start, cur_end, cur_rule, cur_r_end, cur_override))

        for m_start, m_end, rule, m_r_end, m_override in merged:
            # Thu thập ngày làm việc thực tế (bỏ qua kỳ nghỉ điểm 2)
            working_days = []
            curr_date = m_start
            while curr_date <= m_end:
                overlap = False
                for p2_r, _ in point2_leaves:
                    p2_start = max(pd.to_datetime(tf_start), pd.to_datetime(p2_r['start_date']))
                    p2_end = min(pd.to_datetime(tf_end), pd.to_datetime(p2_r['end_date']))
                    if p2_start <= curr_date <= p2_end:
                        overlap = True
                        break
                if not overlap:
                    working_days.append(curr_date)
                curr_date += pd.Timedelta(days=1)

            if working_days:
                blocks = []
                block_start = working_days[0]
                prev_day = working_days[0]
                for day in working_days[1:]:
                    if day == prev_day + pd.Timedelta(days=1):
                        prev_day = day
                    else:
                        blocks.append((block_start, prev_day))
                        block_start = day
                        prev_day = day
                blocks.append((block_start, prev_day))

                inter_weeks = 0.0
                if m_override is not None:
                    inter_weeks = m_override * (len(working_days) / ((m_end - m_start).days + 1))
                else:
                    for b_start, b_end in blocks:
                        inter_weeks += calculate_t04_weeks(b_start, b_end, holidays_list)

                if seg['weeks'] > 0:
                    red_gc = seg['req_gc'] * (rule['teaching_reduction_pct'] / 100.0) * (inter_weeks / seg['weeks'])
                    red_nckh = seg['req_nckh'] * (rule['nckh_reduction_pct'] / 100.0) * (inter_weeks / seg['weeks'])
                else:
                    red_gc = 0.0
                    red_nckh = 0.0

                reduced_gc += red_gc
                reduced_nckh += red_nckh

    for r, rule in point3_leaves:
        desc = f"{rule['name']} ({rule['rule_type']})"
        reductions_desc.append(desc)

    return reduced_gc, reduced_nckh, reductions_desc


def _apply_auto_compensation(row, nckh_to_gc_ratio=3.0, gc_to_nckh_ratio=3.0, min_direct_teaching_ratio=0.5, min_nckh_ratio=0.25):
    gc = row['gc_vuot_thieu']
    nckh = row['nckh_vuot_thieu']
    
    # NCKH deficit, GC excess: compensate NCKH using excess GC (1 GC = gc_to_nckh_ratio NCKH)
    if gc > 0 and nckh < 0:
        nckh_norm = row['dinh_muc_nckh_phai_thuc_hien']
        nckh_done = row['nckh_da_thuc_hien']
        if nckh_norm > 0 and nckh_done >= (nckh_norm * min_nckh_ratio):
            transfer_gc = min(gc, -nckh / gc_to_nckh_ratio)
            return gc - transfer_gc, nckh + (transfer_gc * gc_to_nckh_ratio)
            
    # GC deficit, NCKH excess: compensate GC using excess NCKH (nckh_to_gc_ratio NCKH = 1 GC)
    elif nckh > 0 and gc < 0:
        min_required_teaching = row['dinh_muc_gc_phai_thuc_hien'] * min_direct_teaching_ratio
        direct_teaching = row['giang_day_truc_tiep']
        if direct_teaching >= min_required_teaching:
            transfer_nckh = min(nckh, -gc * nckh_to_gc_ratio)
            return gc + (transfer_nckh / nckh_to_gc_ratio), nckh - transfer_nckh
            
    return gc, nckh


def calculate_teacher_metrics(teacher_id=None, timeframe_id=None, df_session_override=None):
    if df_session_override is not None:
        return _teacher_metrics_impl(teacher_id, timeframe_id, df_session_override)
    return _teacher_metrics_cached(timeframe_id, teacher_id)

@st.cache_data(ttl=300)
def _teacher_metrics_cached(timeframe_id, teacher_id):
    return _teacher_metrics_impl(teacher_id, timeframe_id, None)

def _teacher_metrics_impl(teacher_id, timeframe_id, df_session_override):
    conn = get_connection()
    tf_id, tf_start, tf_end, std_weeks = get_timeframe_dates(timeframe_id)
    
    # Load config constants
    from database import get_setting_value
    nckh_to_gc_ratio = float(get_setting_value('nckh_to_gc_ratio', '3.0'))
    gc_to_nckh_ratio = float(get_setting_value('gc_to_nckh_ratio', '3.0'))
    min_direct_teaching_ratio = float(get_setting_value('min_direct_teaching_ratio', '0.50'))
    min_nckh_ratio = float(get_setting_value('min_nckh_ratio', '0.25'))
    
    if not tf_id:
        conn.close()
        return pd.DataFrame()

    # Load academic holidays for timeframe
    h_query = "SELECT start_date, end_date FROM academic_holidays WHERE timeframe_id = ?"
    df_holidays = pd.read_sql_query(h_query, conn, params=[tf_id])
    holidays_list = []
    for _, h_row in df_holidays.iterrows():
        h_start = pd.to_datetime(h_row['start_date'])
        h_end = pd.to_datetime(h_row['end_date'])
        holidays_list.append((h_start, h_end))

    # Academic vacation: Tết Âm lịch ~3 weeks per Điều 3.2
    # Vacation exclusion is NOT global — only applied per Điều 10.3.c
    # (explicitly stated for thai sản: "23 tuần, không bao gồm 03 tuần nghỉ Tết Âm lịch")


    # Query teachers (core teachers only; GUEST handled separately by payroll)
    t_query = "SELECT * FROM teachers WHERE employment_type IN ('TEACHER', 'STAFF')"
    t_params = []
    if teacher_id is not None:
        t_query += " AND id = ?"
        t_params.append(int(teacher_id))
        
    df_teachers = pd.read_sql_query(t_query, conn, params=t_params)
    if df_teachers.empty:
        conn.close()
        return df_teachers

    # Load titles and reductions rules
    df_titles = pd.read_sql_query("SELECT * FROM titles", conn)
    titles_dict = df_titles.set_index('name').to_dict('index')
    
    df_rules = pd.read_sql_query("SELECT * FROM reduction_rules", conn)
    rules_dict = df_rules.set_index('id').to_dict('index')
    
    df_depts = pd.read_sql_query("SELECT * FROM departments", conn)
    depts_dict = df_depts.set_index('name').to_dict('index')
    
    # Load history
    hist_query = "SELECT * FROM teacher_role_history WHERE start_date <= ? AND (end_date IS NULL OR end_date >= ?)"
    df_hist = pd.read_sql_query(hist_query, conn, params=[tf_end.strftime('%Y-%m-%d'), tf_start.strftime('%Y-%m-%d')])
    df_hist['start_date'] = pd.to_datetime(df_hist['start_date'])
    df_hist['end_date'] = pd.to_datetime(df_hist['end_date']).fillna(pd.to_datetime(tf_end))
    
    results = []
    
    # Iterate teachers
    for _, teacher in df_teachers.iterrows():
        tid = teacher['id']
        t_hist = df_hist[df_hist['teacher_id'] == tid].copy()
        
        # 1. Fetch relevant history records
        title_recs = t_hist[t_hist['record_type'] == 'TITLE'].copy()
        dept_recs = t_hist[t_hist['record_type'] == 'DEPARTMENT'].copy()
        role_recs = t_hist[t_hist['record_type'] == 'REDUCTION'].copy()
        
        segments = _generate_timeline_segments(tf_start, tf_end, title_recs, dept_recs, role_recs, rules_dict)
                
        total_required_gc = 0.0
        total_required_nckh = 0.0
        total_required_nvk = 0.0
        total_reduced_gc = 0.0
        total_reduced_nckh = 0.0
        total_reduced_nvk = 0.0
        applied_reductions = []
        
        seg_data = []
        
        # Determine latest title for display / fallback
        latest_title_name = ""
        latest_base_gc = 0
        latest_base_nckh = 0
        if not title_recs.empty:
            sorted_titles = title_recs.sort_values(by='start_date')
            latest_title_name = sorted_titles.iloc[-1]['value_text']
            if latest_title_name in titles_dict:
                if teacher['subject_group'] == 'Tự nhiên/Kỹ thuật':
                    latest_base_gc = titles_dict[latest_title_name]['base_teaching_hours_natural']
                else:
                    latest_base_gc = titles_dict[latest_title_name]['base_teaching_hours_social']
                latest_base_nckh = titles_dict[latest_title_name]['base_nckh_hours']
                
        for seg_start, seg_end in segments:
            midpoint = seg_start + (seg_end - seg_start) / 2
            
            # Find active TITLE
            title_name = ""
            active_title = title_recs[(title_recs['start_date'] <= midpoint) & (title_recs['end_date'] >= midpoint)]
            if not active_title.empty:
                title_name = active_title.iloc[0]['value_text']
            else:
                # Fallback: if no active title at midpoint, use the latest title that starts before or first overall
                sorted_titles = title_recs.sort_values(by='start_date')
                if not sorted_titles.empty:
                    before_titles = sorted_titles[sorted_titles['start_date'] <= midpoint]
                    if not before_titles.empty:
                        title_name = before_titles.iloc[-1]['value_text']
                    else:
                        title_name = sorted_titles.iloc[0]['value_text']
                        
            # Find active DEPARTMENT
            dept_name = ""
            active_dept = dept_recs[(dept_recs['start_date'] <= midpoint) & (dept_recs['end_date'] >= midpoint)]
            if not active_dept.empty:
                dept_name = active_dept.iloc[0]['value_text']
            else:
                # Fallback
                sorted_depts = dept_recs.sort_values(by='start_date')
                if not sorted_depts.empty:
                    before_depts = sorted_depts[sorted_depts['start_date'] <= midpoint]
                    if not before_depts.empty:
                        dept_name = before_depts.iloc[-1]['value_text']
                    else:
                        dept_name = sorted_depts.iloc[0]['value_text']
                        
            # Find active ROLE
            active_role = None
            role_t_red = 0.0
            role_n_red = 0.0
            role_desc = ""
            for _, r in role_recs.iterrows():
                rid = r['reduction_rule_id']
                if rid in rules_dict and rules_dict[rid]['rule_type'] == 'ROLE':
                    r_start = pd.to_datetime(r['start_date'])
                    r_end = pd.to_datetime(r['end_date'])
                    if r_start <= midpoint <= r_end:
                        active_role = r
                        rule = rules_dict[rid]
                        role_t_red = rule['teaching_reduction_pct']
                        role_n_red = rule['nckh_reduction_pct']
                        role_desc = f"{rule['name']} ({rule['rule_type']})"
                        break
                        
            # Departments that use the natural/technical teaching hours standard
            # (per T04 regulations: natural sciences, techniques, foreign languages, informatics)
            NATURAL_DEPTS = {
                # Legacy generic names (backward compatibility)
                'Tự nhiên, Kỹ thuật, Ngoại ngữ, Tin học',
                'Nhà giáo giảng dạy thực hành',
                # Official Khoa using natural/technical/FL/IT hours
                'Khoa Ngoại ngữ - Tin học',                          # K10
                'Khoa Quân sự, võ thuật, thể dục thể thao',         # K12
            }
            if title_name in titles_dict:
                if dept_name in NATURAL_DEPTS:
                    seg_base_gc = titles_dict[title_name]['base_teaching_hours_natural']
                else:
                    seg_base_gc = titles_dict[title_name]['base_teaching_hours_social']
                seg_base_nckh = titles_dict[title_name]['base_nckh_hours']
            else:
                # Fallback to latest title if active title not found in dictionary
                seg_base_gc = latest_base_gc
                seg_base_nckh = latest_base_nckh
                title_name = latest_title_name
                
            # If active role has override, use it proportionally. Else compute weeks.
            if active_role is not None and pd.notnull(active_role.get('actual_weeks_override')) and active_role.get('actual_weeks_override') != '':
                override = float(active_role['actual_weeks_override'])
                role_start = max(pd.to_datetime(tf_start), pd.to_datetime(active_role['start_date']))
                role_end = min(pd.to_datetime(tf_end), pd.to_datetime(active_role['end_date']))
                total_days = max(1, (role_end - role_start).days + 1)
                seg_days = (seg_end - seg_start).days + 1
                seg_weeks = override * (seg_days / total_days)
            else:
                seg_weeks = calculate_t04_weeks(seg_start, seg_end, holidays_list)
                
            # Non-teaching department defaults
            if dept_name in depts_dict and depts_dict[dept_name]['is_teaching_dept'] == 0:
                if role_t_red < 60.0:
                    role_t_red = 60.0
                    if "Tự động giảm 60% giờ chuẩn (Phòng/Trung tâm)" not in applied_reductions:
                        applied_reductions.append("Tự động giảm 60% giờ chuẩn (Phòng/Trung tâm)")
                if title_name not in ['Giáo sư', 'Phó Giáo sư']:
                    nckh_factor = 0.5
                    if "Giảm 50% NCKH (Phòng/Trung tâm)" not in applied_reductions:
                        applied_reductions.append("Giảm 50% NCKH (Phòng/Trung tâm)")
                else:
                    nckh_factor = 1.0
            else:
                nckh_factor = 1.0
                
            req_gc = seg_base_gc * (1 - role_t_red / 100.0) * (seg_weeks / std_weeks)
            req_nckh = seg_base_nckh * nckh_factor * (1 - role_n_red / 100.0) * (seg_weeks / std_weeks)
            
            seg_yearly_nvk = 1760.0 - (seg_base_gc * (1 - role_t_red / 100.0) * 3.0) - (seg_base_nckh * nckh_factor * (1 - role_n_red / 100.0))
            req_nvk = seg_yearly_nvk * (seg_weeks / std_weeks)
            
            if role_desc and role_desc not in applied_reductions:
                applied_reductions.append(role_desc)
                
            total_required_gc += req_gc
            total_required_nckh += req_nckh
            total_required_nvk += req_nvk
            
            seg_data.append({
                'start': seg_start,
                'end': seg_end,
                'weeks': seg_weeks,
                'req_gc': req_gc,
                'req_nckh': req_nckh,
                'req_nvk': req_nvk,
                'title_name': title_name,
                'dept_name': dept_name
            })
            
            # Automatic reduction for Trợ giảng (Điều 10.3.a)
            tg_red, tg_descs = _calculate_tro_giang_reductions(
                seg_start, seg_end, title_name, title_recs, seg_base_gc, role_t_red, holidays_list, std_weeks
            )
            total_reduced_gc += tg_red
            for desc in tg_descs:
                if desc not in applied_reductions:
                    applied_reductions.append(desc)
                        
        # 2. Distinguish and process Point (2) and Point (3) SPECIAL reductions
        point2_leaves = []
        point3_leaves = []
        
        for _, r in role_recs.iterrows():
            rid = r['reduction_rule_id']
            if rid in rules_dict and rules_dict[rid]['rule_type'] == 'SPECIAL':
                rule = rules_dict[rid]
                if rule['name'].startswith('Trợ giảng'):
                    continue
                if rule['teaching_reduction_pct'] == 100.0:
                    point2_leaves.append((r, rule))
                else:
                    point3_leaves.append((r, rule))
                    
        # Apply Point (2) leaves
        p2_gc, p2_nvk, max_flat_nckh_pct, p2_descs = _calculate_point2_reductions(
            point2_leaves, seg_data, tf_start, tf_end, holidays_list
        )
        total_reduced_gc += p2_gc
        total_reduced_nvk += p2_nvk
        for desc in p2_descs:
            if desc not in applied_reductions:
                applied_reductions.append(desc)

        # Apply Point (3) leaves
        p3_gc, p3_nckh, p3_descs = _calculate_point3_reductions(
            point3_leaves, point2_leaves, seg_data, tf_start, tf_end, holidays_list
        )
        total_reduced_gc += p3_gc
        total_reduced_nckh += p3_nckh
        for desc in p3_descs:
            if desc not in applied_reductions:
                applied_reductions.append(desc)
                
        if max_flat_nckh_pct > 0:
            flat_red_nckh = total_required_nckh * (max_flat_nckh_pct / 100.0)
            total_reduced_nckh += flat_red_nckh
            desc_nckh = f"Giảm NCKH theo năm ({max_flat_nckh_pct}%)"
            if desc_nckh not in applied_reductions:
                applied_reductions.append(desc_nckh)

        total_weeks = sum(s['weeks'] for s in seg_data) if seg_data else 0
        if total_weeks > std_weeks:
            cap = std_weeks / total_weeks
            total_required_gc *= cap
            total_required_nckh *= cap
            total_required_nvk *= cap
            total_reduced_gc *= cap
            total_reduced_nckh *= cap
            total_reduced_nvk *= cap
            cap_alert = f"⚠️ Bị ép định mức (Cap) do năm học dài {total_weeks:.1f} tuần > {std_weeks:.1f} tuần chuẩn"
            if cap_alert not in applied_reductions:
                applied_reductions.append(cap_alert)

        def get_nvk_base_min(title):
            if title in ['Giáo sư', 'Phó Giáo sư']: return 170
            if title == 'Giảng viên chính': return 260
            if title == 'Giảng viên': return 350
            if title == 'Trợ giảng': return 740
            return 0

        results.append({
            'id': tid,
            'title_name': latest_title_name,
            'base_gc': latest_base_gc,
            'base_nckh': latest_base_nckh,
            'dinh_muc_nvk_goc': get_nvk_base_min(latest_title_name),
            'dinh_muc_gc_phai_thuc_hien': total_required_gc,
            'dinh_muc_nckh_phai_thuc_hien': max(0.0, total_required_nckh - total_reduced_nckh),
            'dinh_muc_nvk_phai_thuc_hien': total_required_nvk,
            'so_gio_duoc_mien_giam': total_reduced_gc,
            'so_gio_nvk_duoc_mien_giam': total_reduced_nvk,
            'applied_reductions': ", ".join(applied_reductions) if applied_reductions else "Không có"
        })
        
    df_metrics = pd.DataFrame(results)
    if df_metrics.empty:
        df_metrics = pd.DataFrame(columns=['id', 'base_gc', 'base_nckh', 'dinh_muc_gc_phai_thuc_hien', 'dinh_muc_nckh_phai_thuc_hien'])
    
    df_out = pd.merge(df_teachers, df_metrics, on='id', how='left')
    df_out['dinh_muc_gc_phai_thuc_hien'] = df_out['dinh_muc_gc_phai_thuc_hien'].fillna(0)
    df_out['dinh_muc_nckh_phai_thuc_hien'] = df_out['dinh_muc_nckh_phai_thuc_hien'].fillna(0)
    
    # Tính Logs
    if df_session_override is not None:
        df_session = df_session_override
    else:
        df_session = pd.read_sql_query(
            "SELECT * FROM session_teacher_totals WHERE timeframe_id = ?",
            conn, params=[tf_id]
        )

    if not df_session.empty:
        gc_dict = df_session.set_index('teacher_id')['giang_day_truc_tiep'].to_dict()
        hdcm_bd_dict = df_session.set_index('teacher_id')['hdcm_bd'].to_dict()
        tổng_gc_dict = {
            tid: gc_dict.get(tid, 0.0) + hdcm_bd_dict.get(tid, 0.0)
            for tid in df_session['teacher_id']
        }
        nckh_dict = df_session.set_index('teacher_id')['nckh_total'].to_dict()
        nvk_dict = df_session.set_index('teacher_id')['nvk_total'].to_dict()
        
        df_out['tổng_gc_da_thuc_hien'] = df_out['id'].map(tổng_gc_dict).fillna(0)
        df_out['nckh_da_thuc_hien'] = df_out['id'].map(nckh_dict).fillna(0)
        df_out['nvk_da_thuc_hien'] = df_out['id'].map(nvk_dict).fillna(0)
        df_out['hdcm_bd_da_thuc_hien'] = df_out['id'].map(hdcm_bd_dict).fillna(0)
        df_out['giang_day_truc_tiep'] = df_out['id'].map(gc_dict).fillna(0)
        df_out['nguon_du_lieu'] = 'Excel'
    else:
        query_logs = """
        SELECT 
            al.*, at.category, at.base_conversion_rate, at.is_teaching_activity, at.is_nckh_activity
        FROM activity_logs al
        JOIN activity_types at ON al.activity_type_id = at.id
        WHERE al.timeframe_id = ?
        """
        df_logs = pd.read_sql_query(query_logs, conn, params=[tf_id])
        
        gc_dict = {}
        nckh_dict = {}
        hdcm_bd_dict = {}  # Hoạt động chuyên môn + Bồi dưỡng
        nvk_dict = {} # Nhiệm vụ khác
        direct_teaching_dict = {}
        
        # Per Điều 9 TT108/2025: Hoạt động chuyên môn + Bồi dưỡng count toward GC quota
        GC_CATEGORIES = {'Giảng dạy', 'Hoạt động chuyên môn', 'Bồi dưỡng'}
        NCKH_CATEGORIES = {'NCKH', 'NCKH - Hướng dẫn thi đấu'}
        
        if not df_logs.empty:
            for i, row in df_logs.iterrows():
                hours = calculate_activity_hours(row, row)
                df_logs.at[i, 'calculated_hours'] = hours
                
            for tid, group in df_logs.groupby('teacher_id'):
                gc_dict[tid] = group[group['category'].isin(GC_CATEGORIES)]['calculated_hours'].sum()
                nckh_dict[tid] = group[group['category'].isin(NCKH_CATEGORIES)]['calculated_hours'].sum()
                hdcm_bd_dict[tid] = group[group['category'].isin({'Hoạt động chuyên môn', 'Bồi dưỡng'})]['calculated_hours'].sum()
                nvk_dict[tid] = group[group['category'] == 'Chấp hành Nhiệm vụ khác']['calculated_hours'].sum()
                direct_teaching_dict[tid] = group[group['category'] == 'Giảng dạy']['calculated_hours'].sum()
                
        df_out['tổng_gc_da_thuc_hien'] = df_out['id'].map(gc_dict).fillna(0)
        df_out['nckh_da_thuc_hien'] = df_out['id'].map(nckh_dict).fillna(0)
        df_out['nvk_da_thuc_hien'] = df_out['id'].map(nvk_dict).fillna(0)
        df_out['hdcm_bd_da_thuc_hien'] = df_out['id'].map(hdcm_bd_dict).fillna(0)
        df_out['giang_day_truc_tiep'] = df_out['id'].map(direct_teaching_dict).fillna(0)
        df_out['nguon_du_lieu'] = 'Nhập lẻ'

    # Ghi đè tổng hợp (Aggregate Overrides)
    try:
        df_overrides = pd.read_sql_query(
            "SELECT * FROM teacher_calculated_totals WHERE timeframe_id = ? AND is_override = 1",
            conn, params=[tf_id]
        )
        if not df_overrides.empty:
            for _, ovr in df_overrides.iterrows():
                ovr_tid = ovr['teacher_id']
                idx = df_out[df_out['id'] == ovr_tid].index
                if not idx.empty:
                    df_out.loc[idx, 'tổng_gc_da_thuc_hien'] = ovr['tong_gc_da_thuc_hien']
                    df_out.loc[idx, 'nckh_da_thuc_hien'] = ovr['nckh_da_thuc_hien']
                    df_out.loc[idx, 'so_gio_duoc_mien_giam'] = ovr['so_gio_duoc_mien_giam']
                    df_out.loc[idx, 'dinh_muc_gc_phai_thuc_hien'] = ovr['dinh_muc_gc_phai_thuc_hien']
                    df_out.loc[idx, 'nguon_du_lieu'] = 'Ghi đè (Excel)'
    except Exception:
        pass
    
    df_out['gc_vuot_thieu'] = df_out['tổng_gc_da_thuc_hien'] - (df_out['dinh_muc_gc_phai_thuc_hien'] - df_out['so_gio_duoc_mien_giam'])
    df_out['nckh_vuot_thieu'] = df_out['nckh_da_thuc_hien'] - df_out['dinh_muc_nckh_phai_thuc_hien']
    df_out['nvk_vuot_thieu'] = df_out['nvk_da_thuc_hien'] - (df_out['dinh_muc_nvk_phai_thuc_hien'] - df_out['so_gio_nvk_duoc_mien_giam'])
    df_out['hoan_thanh_gd'] = df_out['gc_vuot_thieu'].apply(lambda x: "Đạt" if x >= 0 else "Không đạt")
    df_out['hoan_thanh_nckh'] = df_out['nckh_vuot_thieu'].apply(lambda x: "Đạt" if x >= 0 else "Không đạt")
    df_out['hoan_thanh_nvk'] = df_out['nvk_vuot_thieu'].apply(lambda x: "Đạt" if x >= 0 else "Không đạt")
    
    def overall_status(row):
        if row['hoan_thanh_gd'] == "Đạt" and row['hoan_thanh_nckh'] == "Đạt" and row['hoan_thanh_nvk'] == "Đạt":
            return "Đạt"
        return "Không đạt"
        
    df_out['trang_thai_chung'] = df_out.apply(overall_status, axis=1)
    
    # Điều 12: Bù trừ tự động giữa Giảng dạy và NCKH
    if not df_out.empty:
        df_out['gc_sau_bu_tru'], df_out['nckh_sau_bu_tru'] = zip(*df_out.apply(
            _apply_auto_compensation, 
            axis=1,
            nckh_to_gc_ratio=nckh_to_gc_ratio,
            gc_to_nckh_ratio=gc_to_nckh_ratio,
            min_direct_teaching_ratio=min_direct_teaching_ratio,
            min_nckh_ratio=min_nckh_ratio
        ))
    else:
        df_out['gc_sau_bu_tru'] = pd.Series(dtype='float64')
        df_out['nckh_sau_bu_tru'] = pd.Series(dtype='float64')
    
    # Tính quy đổi thủ công
    df_conv = pd.read_sql_query("SELECT * FROM manual_conversions WHERE timeframe_id = ?", conn, params=[tf_id])
    
    def apply_conversions(row):
        tid = row['id']
        gc_vt = row['gc_sau_bu_tru']
        nckh_vt = row['nckh_sau_bu_tru']
        
        t_conv = df_conv[df_conv['teacher_id'] == tid]
        for _, c in t_conv.iterrows():
            if c['from_category'] == 'NCKH' and c['to_category'] == 'Giảng dạy':
                gc_vt += c['to_amount']
                nckh_vt -= c['from_amount']
            elif c['from_category'] == 'Giảng dạy' and c['to_category'] == 'NCKH':
                nckh_vt += c['to_amount']
                gc_vt -= c['from_amount']
                
        return pd.Series([gc_vt, nckh_vt])
        
    df_out[['gc_vuot_thieu_sau_quy_doi', 'nckh_vuot_thieu_sau_quy_doi']] = df_out.apply(apply_conversions, axis=1)
    
    conn.close()
    return df_out

def get_conversion_limits(teacher_id, timeframe_id, teacher_row=None):
    """
    Trả về số giờ tối đa có thể quy đổi (Điều 12)
    Có thể truyền teacher_row (từ DataFrame đã có sẵn) để tránh gọi lại calculate_teacher_metrics.
    """
    from database import get_setting_value
    nckh_to_gc_ratio = float(get_setting_value('nckh_to_gc_ratio', '3.0'))
    gc_to_nckh_ratio = float(get_setting_value('gc_to_nckh_ratio', '3.0'))
    min_direct_teaching_ratio = float(get_setting_value('min_direct_teaching_ratio', '0.50'))
    min_nckh_ratio = float(get_setting_value('min_nckh_ratio', '0.25'))

    if teacher_row is not None:
        row = teacher_row
    else:
        df = calculate_teacher_metrics(teacher_id, timeframe_id)
        if df.empty: return None
        row = df.iloc[0]
    res = {
        'can_convert_nckh_to_gc': False,
        'max_nckh_to_spend': 0.0,
        'gc_gained': 0.0,
        'can_convert_gc_to_nckh': False,
        'max_gc_to_spend': 0.0,
        'nckh_gained': 0.0,
        'warning': None
    }
    
    # NCKH -> Giảng dạy (nckh_to_gc_ratio NCKH = 1 GC)
    if row['nckh_vuot_thieu_sau_quy_doi'] > 0 and row['gc_vuot_thieu_sau_quy_doi'] < 0:
        res['can_convert_nckh_to_gc'] = True
        nckh_excess = row['nckh_vuot_thieu_sau_quy_doi']
        gc_deficit = abs(row['gc_vuot_thieu_sau_quy_doi'])
        
        min_required_teaching = row['dinh_muc_gc_phai_thuc_hien'] * min_direct_teaching_ratio

        if row['giang_day_truc_tiep'] >= min_required_teaching:
            nckh_needed = gc_deficit * nckh_to_gc_ratio
            if nckh_excess >= nckh_needed:
                res['max_nckh_to_spend'] = nckh_needed
                res['gc_gained'] = gc_deficit
            else:
                res['max_nckh_to_spend'] = nckh_excess
                res['gc_gained'] = nckh_excess / nckh_to_gc_ratio
        else:
            res['can_convert_nckh_to_gc'] = False
            res['warning'] = f"Không đủ điều kiện: Số giờ giảng trực tiếp ({row['giang_day_truc_tiep']:.1f}) chưa đạt {min_direct_teaching_ratio*100:.0f}% định mức ({min_required_teaching:.1f})."
            
    # Giảng dạy -> NCKH (1 GC = gc_to_nckh_ratio NCKH)
    if row['gc_vuot_thieu_sau_quy_doi'] > 0 and row['nckh_vuot_thieu_sau_quy_doi'] < 0:
        nckh_norm = row['dinh_muc_nckh_phai_thuc_hien']
        nckh_done = row['nckh_da_thuc_hien']
        
        if nckh_done >= (nckh_norm * min_nckh_ratio):
            res['can_convert_gc_to_nckh'] = True
            gc_excess = row['gc_vuot_thieu_sau_quy_doi']
            nckh_deficit = abs(row['nckh_vuot_thieu_sau_quy_doi'])
            
            gc_needed = nckh_deficit / gc_to_nckh_ratio
            if gc_excess >= gc_needed:
                res['max_gc_to_spend'] = gc_needed
                res['nckh_gained'] = nckh_deficit
            else:
                res['max_gc_to_spend'] = gc_excess
                res['nckh_gained'] = gc_excess * gc_to_nckh_ratio
        else:
            res['warning'] = f"Không đủ điều kiện: Phải hoàn thành tối thiểu {min_nckh_ratio*100:.0f}% định mức NCKH mới được quy đổi Giảng dạy bù sang NCKH."
            
    return res

def calculate_department_compensation(df_teachers):
    """
    Áp dụng bù định mức đơn vị (Điều 12.3)
    Chỉ áp dụng cho Giảng dạy (GC).
    """
    df = df_teachers.copy()
    
    if 'dept_name' not in df.columns:
        return df
        
    df['gc_give_to_dept'] = 0.0
    df['gc_receive_from_dept'] = 0.0
    
    for dept, group in df.groupby('dept_name'):
        if dept == 'Chưa phân công': continue
        
        deficits = group[group['gc_vuot_thieu_sau_quy_doi'] < 0]
        excesses = group[group['gc_vuot_thieu_sau_quy_doi'] > 0]
        
        total_deficit = abs(deficits['gc_vuot_thieu_sau_quy_doi'].sum())
        total_excess = excesses['gc_vuot_thieu_sau_quy_doi'].sum()
        
        if total_deficit == 0 or total_excess == 0:
            continue
            
        transfer_amount = min(total_deficit, total_excess)
        
        for idx, row in excesses.iterrows():
            give_amount = transfer_amount * (row['gc_vuot_thieu_sau_quy_doi'] / total_excess)
            df.at[idx, 'gc_vuot_thieu_sau_quy_doi'] -= give_amount
            df.at[idx, 'gc_give_to_dept'] = give_amount
            
        for idx, row in deficits.iterrows():
            receive_amount = transfer_amount * (abs(row['gc_vuot_thieu_sau_quy_doi']) / total_deficit)
            df.at[idx, 'gc_vuot_thieu_sau_quy_doi'] += receive_amount
            df.at[idx, 'gc_receive_from_dept'] = receive_amount
            
    return df

