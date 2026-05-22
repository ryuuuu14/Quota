import sqlite3
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/database.sqlite')

print("--- TABLES ---")
df_tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
print(df_tables)

print("\n--- TEACHERS ---")
df_t = pd.read_sql_query("SELECT * FROM teachers", conn)
print(df_t.to_string())

print("\n--- REDUCTION RULES ---")
df_rr = pd.read_sql_query("SELECT * FROM reduction_rules", conn)
print(df_rr.to_string())

conn.close()
