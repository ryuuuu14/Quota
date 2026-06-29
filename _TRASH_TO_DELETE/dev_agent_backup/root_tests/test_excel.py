import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')
df = pd.read_excel(r'F:\Documents\Documents\Thông tin giảng viên nhập phần mềm.xlsx', header=0)
print(df.columns.tolist())
