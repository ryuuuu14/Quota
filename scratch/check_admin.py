import sqlite3
import bcrypt

conn = sqlite3.connect('data/database.sqlite')
cursor = conn.cursor()
cursor.execute("SELECT password FROM admin_users WHERE username = 'admin'")
pw = cursor.fetchone()[0]
print("Password hash in DB:", pw)
try:
    match = bcrypt.checkpw(b"admin123", pw.encode('utf-8'))
    print("Is admin123?", match)
except Exception as e:
    print("Error checking bcrypt:", e)
conn.close()
