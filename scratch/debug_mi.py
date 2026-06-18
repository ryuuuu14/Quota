import sys
sys.path.append('src')
import sqlite3
import pandas as pd
from calculations import calculate_teacher_metrics

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/database.sqlite')
conn.row_factory = sqlite3.Row

# Get teacher 100 details
t_id = 100
tf_id = 4
df = calculate_teacher_metrics(teacher_id=t_id, timeframe_id=tf_id)
t_metrics = df.iloc[0]

print("--- METRICS FOR TRẦN HOẠ MI ---")
for col in df.columns:
    print(f"{col}: {t_metrics[col]}")

print("\n--- RUNNING INTERNAL HELPER ON TEACHER 100 ---")
from calculations import (
    get_teacher_role_history,
    build_teacher_segments,
    calculate_segment_t04_weeks,
    calculate_t04_weeks,
    get_academic_holidays_list
)

tf_row = conn.execute("SELECT * FROM timeframes WHERE id = ?", (tf_id,)).fetchone()
tf_start = pd.to_datetime(tf_row['start_date'])
tf_end = pd.to_datetime(tf_row['end_date'])
std_weeks = float(tf_row['standard_academic_weeks'])

# Holidays list
holidays_list = get_academic_holidays_list(conn, tf_id)
print(f"Holidays: {holidays_list}")

# Role history
roles = get_teacher_role_history(conn, t_id, tf_start, tf_end)
print("\nRoles:")
print(roles)

# Segments
segments = build_teacher_segments(roles, tf_start, tf_end, holidays_list)
print("\nSegments built:")
for seg in segments:
    print(seg)

# Now, let's check reductions for teacher 100
role_recs = pd.read_sql_query(
    "SELECT * FROM teacher_role_history WHERE teacher_id = ? AND record_type = 'REDUCTION'", 
    conn, params=(t_id,)
)
print("\nReductions records:")
print(role_recs)

# Calculate weeks for the reduction: 2025-10-20 to 2026-05-17
r_start = pd.to_datetime('2025-10-20')
r_end = pd.to_datetime('2026-05-17')

print(f"\nWeeks for reduction block {r_start.date()} to {r_end.date()}:")
r_weeks = calculate_t04_weeks(r_start, r_end, holidays_list)
print(f"T04 Weeks = {r_weeks}")

# Let's check calculations for each segment
for i, seg in enumerate(segments):
    print(f"\nChecking Segment {i}:")
    print(f"  Weeks: {seg['weeks']}")
    o_start = max(seg['start'], r_start)
    o_end = min(seg['end'], r_end)
    if o_start <= o_end:
        o_weeks = calculate_t04_weeks(o_start, o_end, holidays_list)
        print(f"  Overlap with reduction: {o_start.date()} to {o_end.date()}")
        print(f"  Overlap T04 weeks: {o_weeks}")
        
conn.close()
