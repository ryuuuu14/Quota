import sys
sys.path.insert(0, 'src')
from calculations import calculate_teacher_metrics
from database import get_connection
conn = get_connection()
c = conn.cursor()
teacher_id = c.execute("SELECT id FROM teachers WHERE name = 'Bùi Thị X'").fetchone()[0]
timeframe_id = c.execute("SELECT id FROM timeframes WHERE name = 'Năm học 2025-2026'").fetchone()[0]
conn.close()
df = calculate_teacher_metrics(teacher_id=teacher_id, timeframe_id=timeframe_id)
row = df.iloc[0]
print('req_gc:', row['dinh_muc_gc_phai_thuc_hien'])
print('so_gio_duoc_mien_giam:', row['so_gio_duoc_mien_giam'])
