import sqlite3

conn = sqlite3.connect('data/database.sqlite')
cursor = conn.cursor()
cursor.execute("SELECT id, username, role, password_hash FROM users")
print(cursor.fetchall())
conn.close()
