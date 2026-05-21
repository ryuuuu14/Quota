# One-shot script: initialize data/database.sqlite with all seeds
# Run from project root: python scripts/init_data_db.py
import sys, os
# Force DB_PATH to the correct location before importing anything
os.environ['DB_PATH'] = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.sqlite')
db_path = os.path.abspath(os.environ['DB_PATH'])
os.makedirs(os.path.dirname(db_path), exist_ok=True)
print(f"Target DB: {db_path}")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import database
database.DB_PATH = db_path  # override module-level var
database.init_db()
database.seed_initial_data()
print("init_db + seed_initial_data: OK")

# Seed activities
import seed_activities
seed_activities.DB_PATH = db_path
# Patch the get_connection used inside seed_activities
import importlib
import sqlite3

def _get_conn():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

database.get_connection = _get_conn
seed_activities.run()
print("seed_activities: OK")

# Seed reductions — patch its DB_PATH too
import seed_reductions
seed_reductions.DB_PATH = db_path
# seed_reductions uses its own sqlite3.connect(DB_PATH) directly, patch it
import seed_reductions as sr
# Re-read and exec with patched constant
src = open(os.path.join(os.path.dirname(__file__), '..', 'src', 'seed_reductions.py'), encoding='utf-8').read()
src = src.replace("DB_PATH = 'database.sqlite'", f"DB_PATH = r'{db_path}'")
exec(compile(src, 'seed_reductions', 'exec'))
run()  # noqa — defined by exec above
print("seed_reductions: OK")

# Verify
conn = sqlite3.connect(db_path)
counts = {
    'timeframes': conn.execute('SELECT COUNT(*) FROM timeframes').fetchone()[0],
    'titles': conn.execute('SELECT COUNT(*) FROM titles').fetchone()[0],
    'activity_types': conn.execute('SELECT COUNT(*) FROM activity_types').fetchone()[0],
    'reduction_rules': conn.execute('SELECT COUNT(*) FROM reduction_rules').fetchone()[0],
    'departments': conn.execute('SELECT COUNT(*) FROM departments').fetchone()[0],
}
conn.close()
print("\n=== Verification ===")
for k, v in counts.items():
    print(f"  {k}: {v} rows")
print("\nDone! data/database.sqlite is ready.")
