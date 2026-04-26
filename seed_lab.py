import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def seed_lab_assistant():
    conn = sqlite3.connect('data/platform.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO users (name, email, password, role)
        VALUES (?, ?, ?, ?)
        ''', ("Lab Assistant", "lab@example.com", hash_password("lab123"), "lab_assistant"))
        conn.commit()
        print("Lab assistant seeded successfully.")
        print("  Email   : lab@example.com")
        print("  Password: lab123")
    except sqlite3.IntegrityError:
        print("Lab assistant already exists — updating password.")
        cursor.execute('''
        UPDATE users SET password = ? WHERE email = ? AND role = ?
        ''', (hash_password("lab123"), "lab@example.com", "lab_assistant"))
        conn.commit()

    conn.close()

if __name__ == '__main__':
    seed_lab_assistant()
