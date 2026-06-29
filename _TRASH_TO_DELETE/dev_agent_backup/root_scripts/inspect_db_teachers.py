import sqlite3
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('database.sqlite')

print("--- TEACHERS IN DATABASE ---")
df_t = pd.read_sql_query("SELECT * FROM teachers", conn)
print(df_t)

print("\n--- ROLE HISTORY ---")
df_rh = pd.read_sql_query("""
    SELECT rh.*, r.name as rule_name, r.rule_type, r.teaching_reduction_pct, r.nckh_reduction_pct
    FROM teacher_role_history rh
    LEFT JOIN reduction_rules r ON rh.reduction_rule_id = r.id
""", conn)
print(df_rh)

print("\n--- TIMEFRAMES ---")
df_tf = pd.read_sql_query("SELECT * FROM timeframes", conn)
print(df_tf)

print("\n--- HOLIDAYS ---")
df_h = pd.read_sql_query("SELECT * FROM academic_holidays", conn)
print(df_h)

conn.close()
