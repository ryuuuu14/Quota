import sqlite3
import pandas as pd
conn = sqlite3.connect("data/database.sqlite")
df = pd.read_sql_query("SELECT rule_type, name FROM reduction_rules WHERE rule_type='SPECIAL'", conn)
df.to_csv('scratch/special_rules.csv', encoding='utf-8', index=False)
