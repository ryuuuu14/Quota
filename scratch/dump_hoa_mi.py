import sys
import sqlite3
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/database.sqlite')

# Get reduction rule 40
rule = pd.read_sql_query("SELECT * FROM reduction_rules WHERE id = 40", conn)
print("REDUCTION RULE 40:")
print(rule.to_string())

# Let's inspect the active timeframe 
tf = pd.read_sql_query("SELECT * FROM timeframes ORDER BY id DESC LIMIT 1", conn)
print("\nACTIVE TIMEFRAME:")
print(tf.to_string())

# Let's also print active holidays
holidays = pd.read_sql_query("SELECT * FROM academic_holidays WHERE timeframe_id = (SELECT id FROM timeframes ORDER BY id DESC LIMIT 1)", conn)
print("\nHOLIDAYS:")
print(holidays.to_string())

conn.close()
