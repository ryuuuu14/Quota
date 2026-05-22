import sqlite3
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/database.sqlite')

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

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

print("\n--- TITLES ---")
df_title = pd.read_sql_query("SELECT * FROM titles", conn)
print(df_title)

print("\n--- REDUCTION RULES ---")
df_rr = pd.read_sql_query("SELECT * FROM reduction_rules", conn)
print(df_rr)

conn.close()
