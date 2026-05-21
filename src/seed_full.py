"""Seed Full — gộp seed_activities + seed_reductions + seed_initial_data + seed_teachers.
Chạy 1 lần duy nhất: python src/seed_full.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, seed_initial_data, get_connection, DB_PATH
import seed_activities
import seed_reductions
import seed_teachers

def run():
    print(f"Seeding DB: {DB_PATH}")
    init_db()
    print("Tables created OK")

    seed_initial_data()
    print("Settings / timeframes / titles / departments seeded OK")

    # Cleanup old entry renamed during Điều 11 fix
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM reduction_rules WHERE name = 'Đi thực tế / Trưng tập (dưới 10 tháng)'")
    conn.commit()
    conn.close()

    seed_reductions.run()
    seed_activities.run()
    seed_teachers.run()

    # Verify counts
    conn = get_connection()
    c = conn.cursor()
    for t in ['settings', 'timeframes', 'titles', 'departments', 'reduction_rules', 'activity_types']:
        n = c.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  {t}: {n}")
    conn.close()

    print("Done. DB ready at:", DB_PATH)

if __name__ == '__main__':
    run()
