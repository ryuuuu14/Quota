import sys
sys.path.append('src')
from calculations import calculate_teacher_metrics
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
df = calculate_teacher_metrics()
cols = [
    'id', 'name', 'subject_group', 'is_female', 'title_name', 
    'base_gc', 'base_nckh', 'dinh_muc_gc_phai_thuc_hien', 
    'dinh_muc_nckh_phai_thuc_hien', 'so_gio_duoc_mien_giam', 'applied_reductions'
]
print(df[cols].to_string())
