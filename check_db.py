import sqlite3
import os

DB_PATH = 'data/platform.db'

def check_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    print("--- DOCTORS ---")
    doctors = conn.execute('SELECT id, name, pincode FROM users WHERE role = ?', ('doctor',)).fetchall()
    for d in doctors:
        print(dict(d))
        
    print("\n--- PATIENTS ---")
    patients = conn.execute('SELECT id, name, pincode FROM users WHERE role = ?', ('patient',)).fetchall()
    for p in patients:
        print(dict(p))
        
    print("\n--- APPOINTMENTS ---")
    appts = conn.execute('SELECT * FROM appointments').fetchall()
    for a in appts:
        print(dict(a))
        
    conn.close()

if __name__ == '__main__':
    check_data()
