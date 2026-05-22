import sys
sys.path.append('src')
from database import get_connection
from calculations import calculate_teacher_metrics
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

# Let's run calculate_teacher_metrics for Bùi Thị X (ID 53)
df = calculate_teacher_metrics(teacher_id=53)
print(df.to_string())
