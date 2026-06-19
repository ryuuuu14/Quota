import sqlite3
import pandas as pd
from datetime import date
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import get_connection, compute_pro_rata_salary
from calculations import calculate_teacher_metrics

GUEST_RATES = {
    "Ủy viên Bộ Chính trị": 4000000,
    "Ủy viên TW Đảng/Bộ trưởng/Bí thư tỉnh ủy": 3500000,
    "Thứ trưởng/Sĩ quan cấp tướng/Giáo sư/Chuyên gia cao cấp": 3000000,
    "Lãnh đạo cấp Cục/Phó Giáo sư": 2500000,
    "Cán bộ trung ương/tỉnh/Tiến sĩ": 2000000,
    "Đối tượng khác": 1500000,
}


def calculate_guest_pay(guest_rank, converted_hours):
    # TT11 Điều 2.1: 1 buổi = 4 tiết -> rate per hour = rate per session / 4
    rate_per_session = GUEST_RATES.get(guest_rank, 1500000)
    rate_per_hour = rate_per_session / 4.0
    return rate_per_hour * converted_hours


def calculate_thesis_pay(guest_rank, thesis_type, quantity):
    # TT11 Điều 3
    rate_per_session = GUEST_RATES.get(guest_rank, 1500000)
    multiplier = 0.5 if thesis_type == "MASTER" else 1.0
    return (rate_per_session * multiplier) * quantity


def get_hourly_rate(total_12m_salary, standard_hours_annual):
    if not total_12m_salary or not standard_hours_annual or standard_hours_annual == 0:
        return 0
    return (total_12m_salary / standard_hours_annual) * (44.0 / 52.0)


def calculate_base_pay(total_12m_salary, standard_hours_annual, actual_hours):
    if not total_12m_salary or not standard_hours_annual or standard_hours_annual == 0:
        return 0, 0
    base_hours = min(actual_hours, standard_hours_annual)
    rate = get_hourly_rate(total_12m_salary, standard_hours_annual)
    return rate * base_hours, base_hours


def calculate_overtime_pay(total_12m_salary, standard_hours_annual, actual_hours):
    if not total_12m_salary or not standard_hours_annual or standard_hours_annual == 0:
        return 0, 0

    overtime_hours = actual_hours - standard_hours_annual
    if overtime_hours <= 0:
        return 0, 0

    # Cap at 100% standard hours or 100 hours max (Art 4.3)
    capped_overtime = min(overtime_hours, standard_hours_annual, 100)

    rate = get_hourly_rate(total_12m_salary, standard_hours_annual)

    return rate * capped_overtime, capped_overtime


def run_payroll_cycle(timeframe_id, teacher_ids=None):
    result = {
        "guest_count": 0,
        "base_count": 0,
        "overtime_count": 0,
        "total_vnd": 0.0,
        "skipped_no_salary": 0,
        "skipped_no_overtime": 0,
        "skipped_zero_norm": 0,
        "guest_no_activities": 0,
        "guest_no_rank": 0,
        "teacher_no_metrics": 0,
        "activity_count": 0,
        "details": [],
    }
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if any activity logs exist for this timeframe
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM activity_logs WHERE timeframe_id = ?",
            (timeframe_id,),
        )
        result["activity_count"] = cursor.fetchone()["cnt"]

        # Check how many GUEST teachers exist
        guest_count_query = (
            "SELECT COUNT(*) FROM teachers WHERE employment_type = 'GUEST'"
        )
        guest_params_count = []
        if teacher_ids:
            placeholders = ",".join("?" for _ in teacher_ids)
            guest_count_query += f" AND id IN ({placeholders})"
            guest_params_count = list(teacher_ids)
        cursor.execute(guest_count_query, guest_params_count)
        total_guest = cursor.fetchone()[0]
        result["total_guest_count"] = total_guest

        # Check how many TEACHER/STAFF exist
        ts_count_query = "SELECT COUNT(*) FROM teachers WHERE employment_type IN ('TEACHER', 'STAFF')"
        ts_params_count = []
        if teacher_ids:
            placeholders = ",".join("?" for _ in teacher_ids)
            ts_count_query += f" AND id IN ({placeholders})"
            ts_params_count = list(teacher_ids)
        cursor.execute(ts_count_query, ts_params_count)
        total_ts = cursor.fetchone()[0]
        result["total_teacher_count"] = total_ts

        # Clear old records for this timeframe — if filtering by teacher, clear only those
        if teacher_ids:
            placeholders = ",".join("?" for _ in teacher_ids)
            cursor.execute(
                f"DELETE FROM payroll_records WHERE timeframe_id = ? AND teacher_id IN ({placeholders})",
                (timeframe_id, *teacher_ids),
            )
        else:
            cursor.execute(
                "DELETE FROM payroll_records WHERE timeframe_id = ?", (timeframe_id,)
            )

        # 1. Process GUESTS
        guest_query = """
            SELECT al.teacher_id, t.guest_rank, at.name as activity_name, at.category,
                   sum(al.quantity) as total_qty, sum(al.quantity * at.base_conversion_rate) as total_hours
            FROM activity_logs al
            JOIN teachers t ON al.teacher_id = t.id
            JOIN activity_types at ON al.activity_type_id = at.id
            WHERE al.timeframe_id = ? AND t.employment_type = 'GUEST'
        """
        guest_params = [timeframe_id]
        if teacher_ids:
            placeholders = ",".join("?" for _ in teacher_ids)
            guest_query += f" AND al.teacher_id IN ({placeholders})"
            guest_params.extend(teacher_ids)
        guest_query += " GROUP BY al.teacher_id, t.guest_rank, at.name, at.category"
        cursor.execute(guest_query, guest_params)

        guest_logs = cursor.fetchall()
        today_str = date.today().isoformat()

        if total_guest > 0 and not guest_logs:
            result["guest_no_activities"] = total_guest

        for log in guest_logs:
            task_type = log["activity_name"]
            amount = 0
            qty_to_log = 0

            if not log["guest_rank"]:
                result["guest_no_rank"] += 1

            act_name = log["activity_name"]

            if "LV ThS" in act_name or "thạc sĩ" in act_name.lower():
                task_type = "Chấm tốt nghiệp thạc sĩ"
                amount = calculate_thesis_pay(
                    log["guest_rank"], "MASTER", log["total_qty"]
                )
                qty_to_log = log["total_qty"]
            elif "LA TS" in act_name or "tiến sĩ" in act_name.lower():
                task_type = (
                    "Phản biện độc lập luận án tiến sĩ"
                    if "Phản biện" in act_name
                    else "Đánh giá luận án tiến sĩ"
                )
                amount = calculate_thesis_pay(
                    log["guest_rank"], "PHD", log["total_qty"]
                )
                qty_to_log = log["total_qty"]
            elif log["category"] == "Giảng dạy":
                task_type = "Giảng dạy chuyên môn"
                amount = calculate_guest_pay(log["guest_rank"], log["total_hours"])
                qty_to_log = log["total_hours"]
            else:
                amount = calculate_guest_pay(log["guest_rank"], log["total_hours"])
                qty_to_log = log["total_hours"]

            if amount > 0:
                cursor.execute(
                    """
                    INSERT INTO payroll_records (teacher_id, timeframe_id, task_type, quantity, amount_vnd, log_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        log["teacher_id"],
                        timeframe_id,
                        task_type,
                        qty_to_log,
                        amount,
                        today_str,
                    ),
                )
                result["guest_count"] += 1
                result["total_vnd"] += amount

        # 2. Process TEACHER and STAFF — base pay + overtime
        df_metrics = calculate_teacher_metrics(timeframe_id=timeframe_id)

        salary_query = "SELECT id, name, total_12m_salary, salary_coefficient, employment_type FROM teachers WHERE employment_type IN ('TEACHER', 'STAFF')"
        salary_params = []
        if teacher_ids:
            placeholders = ",".join("?" for _ in teacher_ids)
            salary_query += f" AND id IN ({placeholders})"
            salary_params = teacher_ids
        cursor.execute(salary_query, salary_params)
        teacher_salaries = {row["id"]: dict(row) for row in cursor.fetchall()}

        # Track which teacher IDs from metrics have salary records
        if df_metrics is not None and not df_metrics.empty:
            for _, row in df_metrics.iterrows():
                t_id = row["id"]
                if teacher_ids and t_id not in teacher_ids:
                    continue
                if t_id not in teacher_salaries:
                    continue

                t_sal = teacher_salaries[t_id]
                total_12m_salary = t_sal["total_12m_salary"]
                if t_sal["salary_coefficient"] and t_sal["salary_coefficient"] > 0:
                    pro_rata, seg_details = compute_pro_rata_salary(t_id, timeframe_id)
                    if pro_rata:
                        total_12m_salary = pro_rata
                        if len(seg_details) > 1:
                            for sd in seg_details:
                                result["details"].append(f"{t_sal['name']}: {sd}")
                if not total_12m_salary or total_12m_salary <= 0:
                    result["skipped_no_salary"] += 1
                    continue

                actual_hours = row.get("tổng_gc_da_thuc_hien", 0) or 0
                standard_hours = row.get("dinh_muc_gc_phai_thuc_hien", 0) or 0

                if standard_hours <= 0:
                    result["skipped_zero_norm"] += 1
                    continue

                # Base pay for hours worked within quota
                base_amount, base_hours = calculate_base_pay(
                    total_12m_salary, standard_hours, actual_hours
                )
                if base_amount > 0:
                    cursor.execute(
                        """
                        INSERT INTO payroll_records (teacher_id, timeframe_id, task_type, quantity, amount_vnd, log_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            t_id,
                            timeframe_id,
                            "Lương cơ bản theo GC",
                            base_hours,
                            base_amount,
                            today_str,
                        ),
                    )
                    result["base_count"] += 1
                    result["total_vnd"] += base_amount

                # Overtime supplement if actual exceeds standard
                if actual_hours > standard_hours:
                    ot_amount, capped_overtime = calculate_overtime_pay(
                        total_12m_salary, standard_hours, actual_hours
                    )
                    if ot_amount > 0:
                        cursor.execute(
                            """
                            INSERT INTO payroll_records (teacher_id, timeframe_id, task_type, quantity, amount_vnd, log_date)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                            (
                                t_id,
                                timeframe_id,
                                "Vượt định mức GC (Thanh toán cuối năm)",
                                capped_overtime,
                                ot_amount,
                                today_str,
                            ),
                        )
                        result["overtime_count"] += 1
                        result["total_vnd"] += ot_amount
                else:
                    result["skipped_no_overtime"] += 1

            # Count teachers in salary table but not in metrics
            metrics_ids = set(df_metrics["id"].tolist())
            for t_id in teacher_salaries:
                if t_id not in metrics_ids:
                    result["teacher_no_metrics"] += 1

        conn.commit()
        conn.close()

        # Build human-readable details
        d = result["details"]
        if result["activity_count"] == 0:
            d.append("Không có nhật ký hoạt động nào cho kỳ học này.")
        if result["total_guest_count"] == 0 and result["total_teacher_count"] == 0:
            d.append(
                "Không có cán bộ nào trong hệ thống. Hãy thêm cán bộ tại tab Quản lý Cán bộ."
            )
        if result["guest_no_activities"] > 0:
            d.append(
                f"{result['guest_no_activities']} khách mời không có nhật ký hoạt động cho kỳ này."
            )
        if result["guest_no_rank"] > 0:
            d.append("Một số khách mời chưa có cấp bậc (guest_rank).")
        if result["skipped_no_salary"] > 0:
            d.append(
                f"{result['skipped_no_salary']} cán bộ/giảng viên chưa có hệ số lương hoặc tổng lương 12 tháng."
            )
        if result["skipped_zero_norm"] > 0:
            d.append(
                f"{result['skipped_zero_norm']} cán bộ/giảng viên có định mức GC bằng 0 (có thể do thiếu chức danh/chức vụ)."
            )
        if result["skipped_no_overtime"] > 0:
            d.append(
                f"{result['skipped_no_overtime']} cán bộ/giảng viên không có giờ vượt GC."
            )
        if result["teacher_no_metrics"] > 0:
            d.append(
                f"{result['teacher_no_metrics']} cán bộ có lương nhưng không có trong bảng metrics (có thể do không có nhật ký)."
            )

    except Exception as e:
        result["error"] = str(e)
    return result


def get_payroll_records(timeframe_id):
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT pr.id, t.name as teacher_name, t.employment_type, t.guest_rank, 
               pr.task_type, pr.quantity, pr.amount_vnd, pr.log_date
        FROM payroll_records pr
        JOIN teachers t ON pr.teacher_id = t.id
        WHERE pr.timeframe_id = ?
        ORDER BY t.name
    """,
        conn,
        params=(timeframe_id,),
    )
    conn.close()
    return df
