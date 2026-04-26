import sqlite3

def check_users():
    conn = sqlite3.connect('data/platform.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    users = cursor.execute('SELECT email, role, password FROM users').fetchall()
    for user in users:
        print(f"Email: {user['email']}, Role: {user['role']}")
    conn.close()

if __name__ == '__main__':
    check_users()
