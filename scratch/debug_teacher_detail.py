import sys
sys.path.append('src')
import sqlite3
import pandas as pd
from calculations import get_timeframe_dates, calculate_t04_weeks

sys.stdout.reconfigure(encoding='utf-8')


conn = sqlite3.connect('data/database.sqlite')
tf_id, tf_start, tf_end, std_weeks = get_timeframe_dates(conn)

print(f"Timeframe: {tf_start} to {tf_end}, weeks: {std_weeks}")

# Get all teacher role history for teachers
df_hist = pd.read_sql_query("SELECT * FROM teacher_role_history", conn)
df_hist['start_date'] = pd.to_datetime(df_hist['start_date'])
df_hist['end_date'] = pd.to_datetime(df_hist['end_date']).fillna(pd.to_datetime(tf_end))

df_teachers = pd.read_sql_query("SELECT * FROM teachers", conn)
df_titles = pd.read_sql_query("SELECT * FROM titles", conn)
titles_dict = df_titles.set_index('name').to_dict('index')
df_rules = pd.read_sql_query("SELECT * FROM reduction_rules", conn)
rules_dict = df_rules.set_index('id').to_dict('index')

for _, teacher in df_teachers.iterrows():
    tid = teacher['id']
    name = teacher['name']
    print(f"\n==========================================")
    print(f"Teacher: {name} (ID: {tid})")
    
    t_hist = df_hist[df_hist['teacher_id'] == tid].copy()
    
    # Let's see the segments and how they are calculated
    title_recs = t_hist[t_hist['record_type'] == 'TITLE'].copy()
    dept_recs = t_hist[t_hist['record_type'] == 'DEPARTMENT'].copy()
    role_recs = t_hist[t_hist['record_type'] == 'REDUCTION'].copy()
    
    print("\n--- History Records ---")
    print(t_hist[['record_type', 'value_text', 'reduction_rule_id', 'start_date', 'end_date', 'actual_weeks_override']].to_string())
    
    # Re-calculate segments
    dates = set()
    dates.add(pd.to_datetime(tf_start))
    dates.add(pd.to_datetime(tf_end) + pd.Timedelta(days=1))
    
    for r_list in [title_recs, dept_recs]:
        for _, r in r_list.iterrows():
            r_start = max(pd.to_datetime(tf_start), pd.to_datetime(r['start_date']))
            r_end = min(pd.to_datetime(tf_end), pd.to_datetime(r['end_date']))
            if r_start <= r_end:
                dates.add(r_start)
                dates.add(r_end + pd.Timedelta(days=1))

    for _, r in role_recs.iterrows():
        rid = r['reduction_rule_id']
        if rid in rules_dict and rules_dict[rid]['rule_type'] == 'ROLE':
            r_start = max(pd.to_datetime(tf_start), pd.to_datetime(r['start_date']))
            r_end = min(pd.to_datetime(tf_end), pd.to_datetime(r['end_date']))
            if r_start <= r_end:
                dates.add(r_start)
                dates.add(r_end + pd.Timedelta(days=1))
                
    sorted_dates = sorted(list(dates))
    segments = []
    for i in range(len(sorted_dates) - 1):
        seg_start = sorted_dates[i]
        seg_end = sorted_dates[i+1] - pd.Timedelta(days=1)
        if seg_start <= seg_end:
            segments.append((seg_start, seg_end))
            
    print("\n--- Segments ---")
    for start, end in segments:
        weeks = calculate_t04_weeks(start, end)
        print(f"Segment: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')} -> weeks: {weeks}")

conn.close()
