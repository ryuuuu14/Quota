import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')
from database import get_connection
conn = get_connection()
c = conn.cursor()
teacher_id = c.execute("SELECT id FROM teachers WHERE name = 'Bùi Thị X'").fetchone()[0]
timeframe_id = c.execute("SELECT id, start_date, end_date FROM timeframes WHERE name = 'Năm học 2025-2026'").fetchone()[0]
print("Teacher ID:", teacher_id, "Timeframe ID:", timeframe_id)

c.execute("SELECT record_type, value_text, start_date, end_date, actual_weeks_override FROM teacher_role_history WHERE teacher_id = ?", (teacher_id,))
print("History:")
for r in c.fetchall():
    print(dict(r))
conn.close()
