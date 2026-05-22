import sqlite3
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/database.sqlite')

with open('scratch/db_dump.md', 'w', encoding='utf-8') as f:
    f.write("# Database Dump\n\n")
    
    f.write("## Teachers\n\n```\n")
    df_t = pd.read_sql_query("SELECT * FROM teachers", conn)
    f.write(df_t.to_string(index=False) + "\n```\n\n")
    
    f.write("## Role History Columns\n\n```\n")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(teacher_role_history)")
    f.write(str(cursor.fetchall()) + "\n```\n\n")
    
    f.write("## Role History\n\n```\n")
    df_rh = pd.read_sql_query("SELECT * FROM teacher_role_history", conn)
    f.write(df_rh.to_string(index=False) + "\n```\n\n")
    
    f.write("## Timeframes\n\n```\n")
    df_tf = pd.read_sql_query("SELECT * FROM timeframes", conn)
    f.write(df_tf.to_string(index=False) + "\n```\n\n")
    
    f.write("## Academic Holidays\n\n```\n")
    df_h = pd.read_sql_query("SELECT * FROM academic_holidays", conn)
    f.write(df_h.to_string(index=False) + "\n```\n\n")
    
    f.write("## Titles\n\n```\n")
    df_title = pd.read_sql_query("SELECT * FROM titles", conn)
    f.write(df_title.to_string(index=False) + "\n```\n\n")

conn.close()
print("Dumped to scratch/db_dump.md")
