import sqlite3
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/database.sqlite')

print("--- TEACHERS ---")
df_t = pd.read_sql_query("SELECT * FROM teachers", conn)
print(df_t.to_string())

conn.close()
