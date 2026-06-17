import sqlite3
import time
import threading

def thread1():
    print("T1: Connecting...")
    conn1 = sqlite3.connect('data/database.sqlite', timeout=1.0)
    conn1.execute("PRAGMA foreign_keys = ON;")
    try:
        print("T1: Trying to delete TF 1 (will fail)")
        conn1.execute("DELETE FROM timeframes WHERE id = 1")
    except Exception as e:
        print(f"T1: Got {type(e).__name__}: {e}")
    # Intentionally do not rollback or close conn1
    print("T1: Sleeping to hold the connection open...")
    time.sleep(10)

def thread2():
    time.sleep(1) # wait for T1 to fail
    print("T2: Connecting...")
    conn2 = sqlite3.connect('data/database.sqlite', timeout=1.0)
    try:
        print("T2: Trying to insert something...")
        conn2.execute("INSERT INTO departments (name, is_teaching_dept) VALUES ('TEST_DEPT', 1)")
        conn2.commit()
        print("T2: Success")
        conn2.execute("DELETE FROM departments WHERE name = 'TEST_DEPT'")
        conn2.commit()
    except Exception as e:
        print(f"T2: Got {type(e).__name__}: {e}")

t1 = threading.Thread(target=thread1)
t2 = threading.Thread(target=thread2)
t1.start()
t2.start()
t1.join()
t2.join()
