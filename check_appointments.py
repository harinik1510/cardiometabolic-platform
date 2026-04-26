import sqlite3

conn = sqlite3.connect('data/platform.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== APPOINTMENTS ===")
for r in cur.execute("SELECT * FROM appointments"):
    print(dict(r))

conn.close()
