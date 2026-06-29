"""Quick debug: test teacher integration in the real DB."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection
from calculations import calculate_teacher_metrics

conn = get_connection()
c = conn.cursor()

# Check timeframe
print("=== TIMEFRAMES ===")
for row in c.execute("SELECT id, name, start_date, end_date FROM timeframes"):
    print(f"  {row}")

# Check teachers
print("\n=== TEACHERS ===")
for row in c.execute("SELECT id, name, subject_group, is_female FROM teachers"):
    print(f"  {row}")

# Check teacher_role_history
print("\n=== ROLE HISTORY ===")
for row in c.execute("""
    SELECT t.name, h.record_type, h.value_text, h.start_date, h.end_date
    FROM teacher_role_history h
    JOIN teachers t ON h.teacher_id = t.id
    ORDER BY t.name, h.start_date
"""):
    print(
        f"  {row[0]:20s} | {row[1]:12s} | {str(row[2] or ''):30s} | {row[3]} | {row[4] or 'NULL'}"
    )

# Test calculate_teacher_metrics
print("\n=== CALCULATE TEACHER METRICS ===")
df = calculate_teacher_metrics()
print(f"  Columns: {list(df.columns)}")
print(f"  Rows: {len(df)}")
if not df.empty:
    for _, r in df.iterrows():
        print(
            f"  {r['name']:20s} | base_gc={r['base_gc']:.0f} | dinh_muc={r['dinh_muc_gc_phai_thuc_hien']:.1f} | thuc_hien={r['tổng_gc_da_thuc_hien']:.1f} | giam={r['so_gio_duoc_mien_giam']:.1f} | nckh={r['nckh_da_thuc_hien']:.1f}"
        )
else:
    print("  EMPTY! Nothing returned from calculate_teacher_metrics()")

conn.close()
