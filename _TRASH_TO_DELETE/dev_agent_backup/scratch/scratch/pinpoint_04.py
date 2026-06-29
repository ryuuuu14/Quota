import sqlite3
import os
import sys
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

db_path = os.path.join("data", "database.sqlite")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Get holidays
cursor = conn.cursor()
cursor.execute("SELECT * FROM academic_holidays WHERE timeframe_id = 4")
holidays = [dict(row) for row in cursor.fetchall()]

# Period: 20/10/2025 to 17/05/2026
from datetime import date
start = date(2025, 10, 20)
end = date(2026, 5, 17)

# Count every workday
workdays = []
holiday_days = []
weekend_days = []

current = start
while current <= end:
    weekday = current.weekday()  # 0=Mon, 6=Sun
    if weekday >= 5:
        weekend_days.append(current)
        current += timedelta(days=1)
        continue
    
    is_holiday = False
    holiday_name = ""
    for h in holidays:
        h_start = datetime.strptime(h['start_date'], '%Y-%m-%d').date()
        h_end = datetime.strptime(h['end_date'], '%Y-%m-%d').date()
        if h_start <= current <= h_end:
            is_holiday = True
            holiday_name = h['name']
            break
    
    if is_holiday:
        holiday_days.append((current, holiday_name))
    else:
        workdays.append(current)
    
    current += timedelta(days=1)

total_calendar = (end - start).days + 1
total_workdays = len(workdays)
weeks_exact = total_workdays / 5.0
full_weeks = total_workdays // 5
remainder_days = total_workdays % 5

print(f"=== Tran Hoa Mi: Period 20/10/2025 - 17/05/2026 ===")
print(f"Total calendar days: {total_calendar}")
print(f"Weekend days: {len(weekend_days)}")
print(f"Holiday workdays excluded: {len(holiday_days)}")
print(f"Active workdays: {total_workdays}")
print(f"Full weeks (floor): {full_weeks}")
print(f"Remainder days: {remainder_days}")
print(f"Exact weeks: {full_weeks} + {remainder_days}/5 = {weeks_exact}")
print()
print(f"=== THE 0.4 DIFFERENCE ===")
print(f"Manual calc uses: 26 weeks (rounded down)")
print(f"System calc uses: {weeks_exact} weeks (exact)")
print(f"Difference: {weeks_exact - 26.0} weeks = {remainder_days} extra workdays")
print()
print(f"Those {remainder_days} extra days are:")

# The remainder days are the last ones after 26 full weeks (130 days)
# Show which specific days they are
for i, day in enumerate(workdays):
    day_index = i + 1  # 1-based
    if day_index > full_weeks * 5:
        weekday_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'][day.weekday()]
        print(f"  Day #{day_index}: {day.strftime('%Y-%m-%d')} ({weekday_name})")

print()
print(f"=== GC Impact ===")
print(f"At 26.0 weeks: 300 * 26.0 / 44 = {300 * 26.0 / 44:.2f} GC")
print(f"At {weeks_exact} weeks: 300 * {weeks_exact} / 44 = {300 * weeks_exact / 44:.2f} GC")
print(f"Delta: {300 * weeks_exact / 44 - 300 * 26.0 / 44:.2f} GC")

conn.close()
