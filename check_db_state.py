import sqlite3

conn = sqlite3.connect('data/platform.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check what tables exist
print("=== TABLES IN DB ===")
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    print(f"  {t['name']}")

print()
print("=== NOTIFICATIONS ===")
for r in cur.execute("SELECT id, user_id, message, type FROM notifications"):
    print(f"  id={r['id']}, user={r['user_id']}, type={r['type']}, msg={r['message'][:60]}")

print()
print("=== LAB UPLOADS (if table exists) ===")
try:
    for r in cur.execute("SELECT * FROM lab_uploads"):
        print(dict(r))
except Exception as e:
    print(f"  ERROR: {e}")

conn.close()
