import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in [os.path.join(root, 'data', 'database.sqlite'), os.path.join(root, 'database.sqlite')]:
    if os.path.exists(p):
        db_path = p
        break
print('Using DB:', db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
tables = [t[0] for t in cursor.fetchall()]
print('=== ALL TABLES ===')
for t in tables:
    print(' -', t)

print()
for t in tables:
    cursor.execute('SELECT sql FROM sqlite_master WHERE name=?', (t,))
    sql = cursor.fetchone()[0]
    print('--- ' + t + ' ---')
    print(sql)
    print()

print('=== ALL INDEXES ===')
cursor.execute('SELECT name, sql FROM sqlite_master WHERE type="index" AND sql IS NOT NULL')
for idx in cursor.fetchall():
    print(idx[0] + ': ' + idx[1])

print()
print('=== FOREIGN KEY RELATIONSHIPS ===')
for t in tables:
    cursor.execute('PRAGMA foreign_key_list("' + t + '")')
    fks = cursor.fetchall()
    if fks:
        print('--- ' + t + ' ---')
        for fk in fks:
            print(f'  FK id={fk[0]}, seq={fk[1]}, table={fk[2]}, from={fk[3]}, to={fk[4]}, on_update={fk[5]}, on_delete={fk[6]}, match={fk[7]}')

conn.close()
