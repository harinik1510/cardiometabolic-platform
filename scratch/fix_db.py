import sqlite3
import os

DB_PATH = 'data/platform.db'
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE appointments SET prescription_path = 'prescription_record.txt'")
    conn.commit()
    conn.close()
    print("Database updated successfully.")
else:
    print("Database not found.")
