import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

class MySQLConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=None):
        # Convert SQLite '?' placeholder to MySQL '%s'
        query = query.replace('?', '%s')
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def cursor(self, **kwargs):
        return self.conn.cursor(**kwargs)

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('TIDB_HOST'),
            port=int(os.getenv('TIDB_PORT', 4000)),
            user=os.getenv('TIDB_USER'),
            password=os.getenv('TIDB_PASSWORD'),
            database=os.getenv('TIDB_DB_NAME'),
            ssl_verify_cert=False,
            autocommit=True
        )
        return MySQLConnectionWrapper(conn)
    except Exception as e:
        print(f"CRITICAL: Failed to connect to TiDB: {e}")
        return None

def init_db():
    conn_wrapper = get_db_connection()
    if not conn_wrapper:
        print("Failed to connect to TiDB for initialization.")
        return
        
    conn = conn_wrapper.conn
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        pincode VARCHAR(20),
        phone VARCHAR(20),
        age INT,
        gender VARCHAR(20),
        city VARCHAR(100),
        specialization VARCHAR(255),
        experience INT,
        fees DECIMAL(10, 2),
        caretaker_id INT,
        FOREIGN KEY (caretaker_id) REFERENCES users (id)
    ) ENGINE=InnoDB;
    ''')

    # Health Reports
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS health_reports (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT NOT NULL,
        report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fasting_blood_sugar FLOAT,
        hba1c FLOAT,
        total_cholesterol FLOAT,
        ldl FLOAT,
        hdl FLOAT,
        triglycerides FLOAT,
        blood_pressure VARCHAR(50),
        bmi FLOAT,
        creatinine FLOAT,
        ecg_result VARCHAR(50),
        smoking_habit VARCHAR(50),
        alcohol_consumption VARCHAR(50),
        pcos_diagnosed VARCHAR(50),
        gestational_diabetes VARCHAR(50),
        risk_level VARCHAR(100),
        predicted_diseases TEXT,
        analysis_graph_path VARCHAR(255),
        FOREIGN KEY (patient_id) REFERENCES users (id)
    ) ENGINE=InnoDB;
    ''')

    # Appointments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT NOT NULL,
        doctor_id INT NOT NULL,
        appointment_date DATE NOT NULL,
        appointment_time TIME NOT NULL,
        symptoms TEXT,
        status VARCHAR(50) DEFAULT 'pending',
        consultation_start_time TIMESTAMP NULL DEFAULT NULL,
        prescription_path VARCHAR(255),
        prescription_text TEXT,
        FOREIGN KEY (patient_id) REFERENCES users (id),
        FOREIGN KEY (doctor_id) REFERENCES users (id)
    ) ENGINE=InnoDB;
    ''')

    # Notifications
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        message TEXT NOT NULL,
        type VARCHAR(50),
        is_read TINYINT(1) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    ) ENGINE=InnoDB;
    ''')

    # Lab Uploads
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lab_uploads (
        id INT AUTO_INCREMENT PRIMARY KEY,
        lab_assistant_id INT NOT NULL,
        patient_email VARCHAR(255) NOT NULL,
        file_path VARCHAR(255) NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lab_assistant_id) REFERENCES users (id)
    ) ENGINE=InnoDB;
    ''')

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("TiDB Database initialized successfully.")
