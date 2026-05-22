import sys
sys.path.append('src')
from calculations import calculate_t04_weeks
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
hols = [] # no holidays in DB
print("Trưng tập: 2025-09-01 to 2025-12-28")
w_trung_tap = calculate_t04_weeks('2025-09-01', '2025-12-28', hols)
print("Weeks:", w_trung_tap)

print("Bồi dưỡng: 2025-10-27 to 2025-11-17")
w_boi_duong = calculate_t04_weeks('2025-10-27', '2025-11-17', hols)
print("Weeks:", w_boi_duong)

print("Điều trị bệnh: 2026-04-06 to 2026-04-27")
w_benh = calculate_t04_weeks('2026-04-06', '2026-04-27', hols)
print("Weeks:", w_benh)
