import sqlite3
import hashlib

conn = sqlite3.connect('data/platform.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

PATIENT_EMAIL = 'kharini1510@gmail.com'
PATIENT_ID = 47
LAB_ASSISTANT_ID = 48  # lab@example.com user id (set to 1 if unknown, we'll look it up)

# Look up lab assistant id
lab = cur.execute("SELECT id FROM users WHERE role='lab_assistant' LIMIT 1").fetchone()
lab_id = lab['id'] if lab else 1
print(f"Lab assistant id: {lab_id}")

# Files that exist on disk
existing_files = [
    ('lab_kharini1510@gmail.com_High_Risk_Health_Report.pdf', '2026-04-23 09:02:23'),
    ('lab_kharini1510@gmail.com_Full_Body_Checkup_Report.pdf', '2026-04-23 09:56:33'),
]

# Insert into lab_uploads if not already there
for fname, upload_date in existing_files:
    exists = cur.execute("SELECT id FROM lab_uploads WHERE file_path = ?", (fname,)).fetchone()
    if not exists:
        cur.execute(
            "INSERT INTO lab_uploads (lab_assistant_id, patient_email, file_path, upload_date) VALUES (?, ?, ?, ?)",
            (lab_id, PATIENT_EMAIL, fname, upload_date))
        print(f"Inserted lab_upload: {fname}")
    else:
        print(f"Already exists: {fname}")

# Fix existing notification (id=4) to reference the most recent file
cur.execute(
    "UPDATE notifications SET type=?, message=? WHERE id=4",
    (f"report_upload:lab_kharini1510@gmail.com_Full_Body_Checkup_Report.pdf",
     'A new lab report "Full_Body_Checkup_Report.pdf" has been uploaded for you.'))
print("Updated notification id=4 to reference Full_Body_Checkup_Report.pdf")

# Create a second notification for the older file if not already there
old_notif = cur.execute(
    "SELECT id FROM notifications WHERE type=? AND user_id=?",
    (f"report_upload:lab_kharini1510@gmail.com_High_Risk_Health_Report.pdf", PATIENT_ID)).fetchone()
if not old_notif:
    cur.execute(
        "INSERT INTO notifications (user_id, message, type, is_read, created_at) VALUES (?, ?, ?, ?, ?)",
        (PATIENT_ID,
         'A new lab report "High_Risk_Health_Report.pdf" has been uploaded for you.',
         'report_upload:lab_kharini1510@gmail.com_High_Risk_Health_Report.pdf',
         1, '2026-04-23 09:02:23'))
    print("Created notification for High_Risk_Health_Report.pdf")

conn.commit()
conn.close()
print("\nDone! Both reports are now linked and downloadable from Notifications.")
