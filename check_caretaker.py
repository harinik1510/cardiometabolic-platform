import sqlite3
conn = sqlite3.connect('data/platform.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print('=== CARETAKERS ===')
rows = cur.execute("SELECT id, name, email, role FROM users WHERE role='caretaker'").fetchall()
for r in rows:
    print(f"  id={r['id']}, name={r['name']}, email={r['email']}")

print()
print('=== PATIENTS ===')
rows = cur.execute("SELECT id, name, email, caretaker_id FROM users WHERE role='patient'").fetchall()
for r in rows:
    print(f"  id={r['id']}, name={r['name']}, email={r['email']}, caretaker_id={r['caretaker_id']}")

conn.close()
