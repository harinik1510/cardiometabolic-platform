from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import os
from datetime import datetime
from database import get_db_connection, init_db

# Initialize database on startup
init_db()

app = Flask(__name__)
app.secret_key = 'your_super_secret_key' # In production, use an environment variable
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def simulate_report_data(age, gender, filename):
    import random
    filename = filename.lower()
    # Heuristic: Determine simulation target based on filename
    if 'high' in filename or 'critical' in filename:
        fbs, hba1c, sys_bp, bmi = random.randint(140, 200), round(random.uniform(7.0, 10.0), 1), random.randint(145, 170), round(random.uniform(31.0, 38.0), 1)
        chol, ldl, trig = random.randint(240, 300), random.randint(160, 220), random.randint(200, 400)
    elif 'mod' in filename or 'medium' in filename:
        fbs, hba1c, sys_bp, bmi = random.randint(110, 135), round(random.uniform(5.8, 6.4), 1), random.randint(125, 140), round(random.uniform(26.0, 30.0), 1)
        chol, ldl, trig = random.randint(200, 239), random.randint(130, 159), random.randint(150, 199)
    else: # Default to low risk simulation
        fbs, hba1c, sys_bp, bmi = random.randint(80, 105), round(random.uniform(4.5, 5.6), 1), random.randint(110, 120), round(random.uniform(20.0, 24.5), 1)
        chol, ldl, trig = random.randint(150, 199), random.randint(70, 129), random.randint(100, 149)

    return {
        'age': age, 'gender': gender,
        'fbs': fbs, 'hba1c': hba1c, 
        'chol': chol, 'ldl': ldl, 
        'hdl': random.randint(40, 60), 'trig': trig,
        'sys_bp': sys_bp, 'dia_bp': random.randint(70, 90), 
        'bmi': bmi, 'creatinine': round(random.uniform(0.7, 1.2), 1),
        'smoking': 0, 'alcohol': 0
    }

def process_and_save_analysis(patient_id, report_data):
    from models_ml import predict_risk
    results = predict_risk(report_data)
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO health_reports (
            patient_id, fasting_blood_sugar, hba1c, total_cholesterol, ldl, hdl, 
            triglycerides, blood_pressure, bmi, creatinine, 
            smoking_habit, alcohol_consumption, risk_level, predicted_diseases
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_id, report_data['fbs'], report_data['hba1c'], report_data['chol'], 
        report_data['ldl'], report_data['hdl'], report_data['trig'], 
        f"{report_data['sys_bp']}/{report_data['dia_bp']}", 
        report_data['bmi'], report_data['creatinine'],
        'regular' if report_data['smoking'] else 'never',
        'moderate' if report_data['alcohol'] else 'none',
        results['final_prediction'],
        ', '.join(results['predicted_diseases'])
    ))
    conn.commit()
    conn.close()
    return results

@app.route('/')
def index():
    return render_template('role_selection.html')

@app.route('/auth/<role>')
def auth(role):
    if role not in ['patient', 'doctor', 'caretaker', 'lab_assistant']:
        return redirect(url_for('index'))
    return render_template('auth.html', role=role)

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = hash_password(request.form.get('password'))
    role = request.form.get('role')

    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again later.', 'danger')
        return redirect(url_for('auth', role=role))
        
    try:
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ? AND role = ?',
                            (email, password, role)).fetchone()
        conn.close()
    except Exception as e:
        return f"<h1>SQL Error during Login:</h1><p>The app connected to TiDB successfully, but the query failed. Error details: <br><b>{str(e)}</b></p><br><p>This usually means the tables were not created properly.</p>"


    if user:
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['name'] = user['name']
        session['gender'] = user['gender']
        
        if role == 'patient':
            # Check if profile is complete
            if not user['age'] or not user['gender']:
                return redirect(url_for('patient_details'))
            return redirect(url_for('patient_dashboard'))
        elif role == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        elif role == 'caretaker':
            return redirect(url_for('caretaker_dashboard'))
        elif role == 'lab_assistant':
            return redirect(url_for('lab_assistant_dashboard'))
    
    flash('Invalid credentials or role', 'danger')
    return redirect(url_for('auth', role=role))

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = hash_password(request.form.get('password'))
    role = 'patient' # Only patients can register through the UI

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                     (name, email, password, role))
        conn.commit()
        flash('Registration successful! Please login.', 'success')
    except Exception as e:
        print(f"Registration error: {e}")
        return f"<h1>SQL Error during Registration:</h1><p>The app connected to TiDB successfully, but the insert query failed. Error details: <br><b>{str(e)}</b></p>"
    finally:
        conn.close()

    
    return redirect(url_for('auth', role=role))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- Patient Routes ---

@app.route('/patient/details', methods=['GET', 'POST'])
def patient_details():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        age = request.form.get('age')
        gender = request.form.get('gender')
        city = request.form.get('city')
        pincode = request.form.get('pincode')
        wants_caretaker = request.form.get('wants_caretaker') == 'yes'
        
        conn = get_db_connection()
        conn.execute('UPDATE users SET age = ?, gender = ?, city = ?, pincode = ? WHERE id = ?',
                     (age, gender, city, pincode, session['user_id']))
        session['gender'] = gender
        
        if wants_caretaker:
            ct_name = request.form.get('caretaker_name')
            ct_email = request.form.get('caretaker_email')
            if ct_name and ct_email:
                ct_password = hash_password(ct_name + '123')
                # Check if caretaker already exists
                existing_ct = conn.execute(
                    'SELECT id FROM users WHERE email = ? AND role = ?',
                    (ct_email, 'caretaker')).fetchone()
                if existing_ct:
                    ct_id = existing_ct['id']
                    # Update name/password in case they changed
                    conn.execute('UPDATE users SET name = ?, password = ? WHERE id = ?',
                                 (ct_name, ct_password, ct_id))
                else:
                    conn.execute(
                        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                        (ct_name, ct_email, ct_password, 'caretaker'))
                    ct_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                # Link patient to caretaker
                conn.execute('UPDATE users SET caretaker_id = ? WHERE id = ?',
                             (ct_id, session['user_id']))

        conn.commit()
        conn.close()
        return redirect(url_for('patient_dashboard'))

    return render_template('patient_details.html')

@app.route('/patient/dashboard')
def patient_dashboard():
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return redirect(url_for('index'))
    
    # Use managed patient if in caretaker mode
    is_caretaker = (session.get('role') == 'caretaker' and session.get('managed_patient_id'))
    target_id = session.get('managed_patient_id', session['user_id'])
    patient_name = session.get('managed_patient_name') if is_caretaker else session['name']
    
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT a.*, u.name as doctor_name, u.specialization 
        FROM appointments a
        JOIN users u ON a.doctor_id = u.id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
        LIMIT 2
    ''', (target_id,)).fetchall()
    
    latest_report = conn.execute('''
        SELECT * FROM health_reports 
        WHERE patient_id = ? 
        ORDER BY report_date DESC LIMIT 1
    ''', (target_id,)).fetchone()
    
    # Fetch latest 2 lab reports
    patient_email_row = conn.execute('SELECT email FROM users WHERE id = ?', (target_id,)).fetchone()
    latest_uploads = []
    if patient_email_row:
        latest_uploads = conn.execute('''
            SELECT * FROM lab_uploads 
            WHERE patient_email = ? 
            ORDER BY upload_date DESC LIMIT 2
        ''', (patient_email_row['email'],)).fetchall()
    
    # Fetch latest digital prescription
    latest_presc = conn.execute('''
        SELECT a.*, u.name as doctor_name FROM appointments a
        JOIN users u ON a.doctor_id = u.id
        WHERE a.patient_id = ? AND a.status = 'completed'
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
        LIMIT 1
    ''', (target_id,)).fetchone()
    
    conn.close()

    return render_template('patient_dashboard.html', 
                           active_page='dashboard',
                           is_caretaker=is_caretaker,
                           managed_patient_id=target_id if is_caretaker else None,
                           patient_name=patient_name,
                           recent_appointments=appointments,
                           latest_report=latest_report,
                           recent_reports=latest_uploads,
                           latest_prescription=latest_presc)

@app.route('/patient/analyze', methods=['POST'])
def analyze_report():
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return redirect(url_for('index'))
        
    is_caretaker = (session.get('role') == 'caretaker')
    
    # Check if a caretaker is submitting for a managed patient
    managed_id = request.form.get('managed_patient_id')
    target_user_id = int(managed_id) if managed_id else session['user_id']
    
    conn = get_db_connection()
    user = conn.execute('SELECT age, gender FROM users WHERE id = ?', (target_user_id,)).fetchone()
    conn.close()

    user_age = user['age'] if user and user['age'] else 35
    user_gender = 0 if user and user['gender'] == 'male' else 1
    
    # Update managed context only if we are in caretaker mode
    if is_caretaker and managed_id:
        session['managed_patient_id'] = int(managed_id)
    elif not is_caretaker:
        session.pop('managed_patient_id', None)
    
    # Check if it's a report upload or manual entry
    if 'report' in request.files and request.files['report'].filename != '':
        report_data = simulate_report_data(user_age, user_gender, request.files['report'].filename)
    else:
        # Handle manual entry
        bp = request.form.get('bp', '120/80').split('/')
        sys_bp = int(bp[0]) if len(bp) > 0 else 120
        dia_bp = int(bp[1]) if len(bp) > 1 else 80
        
        report_data = {
            'age': user_age,
            'gender': user_gender,
            'fbs': float(request.form.get('fbs', 100)),
            'hba1c': float(request.form.get('hba1c', 5.5)),
            'chol': float(request.form.get('chol', 200)),
            'ldl': float(request.form.get('ldl', 120)),
            'hdl': float(request.form.get('hdl', 50)),
            'trig': float(request.form.get('trig', 150)),
            'sys_bp': sys_bp,
            'dia_bp': dia_bp,
            'bmi': float(request.form.get('bmi', 24.5)),
            'creatinine': float(request.form.get('creatinine', 1.0)),
            'smoking': 1 if request.form.get('smoking') != 'never' else 0,
            'alcohol': 1 if request.form.get('alcohol') != 'none' else 0
        }

    results = process_and_save_analysis(target_user_id, report_data)
    
    # Store results in session for the results page
    session['analysis_results'] = results
    session['report_data'] = report_data
    
    return redirect(url_for('analysis_results'))

@app.route('/patient/results')
def analysis_results():
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return redirect(url_for('index'))
    
    target_user_id = session.get('managed_patient_id', session['user_id'])
    
    if 'analysis_results' not in session:
        # Try to load the latest analysis from DB
        conn = get_db_connection()
        latest = conn.execute('''
            SELECT * FROM health_reports 
            WHERE patient_id = ? 
            ORDER BY report_date DESC LIMIT 1
        ''', (target_user_id,)).fetchone()
        conn.close()
        
        if latest:
            # Reconstruct the report_data object in the format models_ml expects
            bp = latest['blood_pressure'].split('/')
            
            # We need age and gender from the users table for accurate contributor calculation
            conn = get_db_connection()
            user_info = conn.execute('SELECT age, gender FROM users WHERE id = ?', (target_user_id,)).fetchone()
            conn.close()
            
            report_data = {
                'age': user_info['age'] if user_info and user_info['age'] else 35,
                'gender': 0 if user_info and user_info['gender'] == 'male' else 1,
                'fbs': latest['fasting_blood_sugar'],
                'hba1c': latest['hba1c'],
                'chol': latest['total_cholesterol'],
                'ldl': latest['ldl'],
                'hdl': latest['hdl'],
                'trig': latest['triglycerides'],
                'sys_bp': int(bp[0]),
                'dia_bp': int(bp[1]),
                'bmi': latest['bmi'],
                'creatinine': latest['creatinine'],
                'smoking': 1 if latest['smoking_habit'] == 'regular' else 0,
                'alcohol': 1 if latest['alcohol_consumption'] == 'moderate' or latest['alcohol_consumption'] == 'heavy' else 0
            }
            
            # Re-run the risk calculation to get all necessary fields (contributors, etc.)
            from models_ml import predict_risk
            results = predict_risk(report_data)
            
            session['analysis_results'] = results
            session['report_data'] = report_data
        else:
            flash('No analysis records found. Please submit your health data first.', 'info')
            return redirect(url_for('patient_dashboard'))
    
    is_caretaker = False
    patient_name = ""
    if 'managed_patient_id' in session and session['managed_patient_id']:
        is_caretaker = True
        conn = get_db_connection()
        patient = conn.execute('SELECT name FROM users WHERE id = ?', (session['managed_patient_id'],)).fetchone()
        conn.close()
        patient_name = patient['name'] if patient else "Patient"

    return render_template('analysis_results.html', 
                           results=session['analysis_results'],
                           data=session['report_data'],
                           is_caretaker=is_caretaker,
                           patient_name=patient_name,
                           active_page='analysis')

@app.route('/patient/lifestyle')
def lifestyle_advice():
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return redirect(url_for('index'))
    
    target_user_id = session.get('managed_patient_id', session['user_id'])
    
    if 'analysis_results' not in session:
        # Try to load latest risk from DB
        conn = get_db_connection()
        latest = conn.execute('''
            SELECT risk_level FROM health_reports 
            WHERE patient_id = ? 
            ORDER BY report_date DESC LIMIT 1
        ''', (target_user_id,)).fetchone()
        conn.close()
        
        if latest:
            risk_val = 2 if latest['risk_level'] == 'High Risk' else 1 if latest['risk_level'] == 'Moderate Risk' else 0
            return render_template('lifestyle_advice.html', risk=risk_val, active_page='lifestyle')
        else:
            flash('No analysis records found. Please submit your health data first.', 'info')
            return redirect(url_for('patient_dashboard'))
    
    risk = session['analysis_results']['rf_raw']
    return render_template('lifestyle_advice.html', risk=risk, active_page='lifestyle')

@app.route('/patient/select_doctor')
def select_doctor():
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return redirect(url_for('index'))
    
    # Use managed patient if in caretaker mode
    target_user_id = session.get('managed_patient_id', session['user_id'])
    
    conn = get_db_connection()
    user = conn.execute('SELECT pincode FROM users WHERE id = ?', (target_user_id,)).fetchone()
    user_pincode = user['pincode'] if user else None
    
    # Show doctors in the patient's pincode by default
    doctors = []
    if user_pincode:
        doctors = conn.execute('SELECT * FROM users WHERE role = ? AND pincode = ?', 
                               ('doctor', user_pincode)).fetchall()
    
    # If no doctors found in pincode, show all doctors
    if not doctors:
        doctors = conn.execute('SELECT * FROM users WHERE role = ?', ('doctor',)).fetchall()
    
    conn.close()
    return render_template('select_doctor.html', doctors=doctors, pincode=user_pincode, active_page='select_doctor')

@app.route('/patient/book_appointment', methods=['POST'])
def book_appointment():
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return redirect(url_for('index'))
    
    doctor_id = request.form.get('doctor_id')
    date = request.form.get('date')
    time = request.form.get('time')
    symptoms = request.form.get('symptoms')
    
    # Use managed patient if in caretaker mode
    target_user_id = session.get('managed_patient_id', session['user_id'])
    
    conn = get_db_connection()
    conn.execute('INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, symptoms) VALUES (?, ?, ?, ?, ?)',
                 (target_user_id, doctor_id, date, time, symptoms))
    conn.commit()
    conn.close()
    
    flash('Appointment request sent! You will be notified once accepted.', 'success')
    return redirect(url_for('patient_dashboard'))

@app.route('/patient/profile', methods=['GET', 'POST'])
def patient_profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        city = request.form.get('city')
        pincode = request.form.get('pincode')
        
        conn.execute('UPDATE users SET name = ?, age = ?, gender = ?, city = ?, pincode = ? WHERE id = ?',
                     (name, age, gender, city, pincode, session['user_id']))
        session['name'] = name
        session['gender'] = gender

        # Handle caretaker update
        ct_name = request.form.get('caretaker_name', '').strip()
        ct_email = request.form.get('caretaker_email', '').strip()
        if ct_name and ct_email:
            ct_password = hash_password(ct_name + '123')
            existing_ct = conn.execute(
                'SELECT id FROM users WHERE email = ? AND role = ?',
                (ct_email, 'caretaker')).fetchone()
            if existing_ct:
                ct_id = existing_ct['id']
                conn.execute('UPDATE users SET name = ?, password = ? WHERE id = ?',
                             (ct_name, ct_password, ct_id))
            else:
                conn.execute(
                    'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                    (ct_name, ct_email, ct_password, 'caretaker'))
                ct_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            conn.execute('UPDATE users SET caretaker_id = ? WHERE id = ?',
                         (ct_id, session['user_id']))

        conn.commit()
        flash('Profile updated successfully!', 'success')
    
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    # Fetch linked caretaker info
    caretaker = None
    if user['caretaker_id']:
        caretaker = conn.execute(
            'SELECT name, email FROM users WHERE id = ?', (user['caretaker_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user, caretaker=caretaker, active_page='profile')

@app.route('/patient/notifications')
def notifications():
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return redirect(url_for('index'))
    
    # Use managed patient if in caretaker mode
    target_user_id = session.get('managed_patient_id', session['user_id'])
    
    conn = get_db_connection()
    notes = conn.execute('SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC', 
                         (target_user_id,)).fetchall()
    # Mark as read
    conn.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (target_user_id,))
    conn.commit()
    conn.close()
    return render_template('notifications.html', notifications=notes, active_page='notifications')

@app.route('/patient/notifications/dismiss/<int:notif_id>')
def dismiss_notification(notif_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    target_user_id = session.get('managed_patient_id', session['user_id'])
    conn = get_db_connection()
    conn.execute('DELETE FROM notifications WHERE id = ? AND user_id = ?',
                 (notif_id, target_user_id))
    conn.commit()
    conn.close()
    # If request came from the dropdown (AJAX-style), redirect back to wherever they were
    return redirect(request.referrer or url_for('notifications'))

@app.route('/api/notifications')
def api_notifications():
    """Return notifications as JSON for the bell dropdown."""
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return jsonify({'notifications': []})
    target_user_id = session.get('managed_patient_id', session['user_id'])
    conn = get_db_connection()
    notes = conn.execute(
        'SELECT id, message, type, is_read, created_at FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 20',
        (target_user_id,)).fetchall()
    # Mark all as read once the user opens the dropdown
    conn.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (target_user_id,))
    conn.commit()
    conn.close()
    return jsonify({
        'notifications': [
            {'id': n['id'], 'message': n['message'], 'type': n['type'],
             'is_read': bool(n['is_read']), 'created_at': n['created_at']}
            for n in notes
        ]
    })

@app.route('/api/notifications/count')
def api_notifications_count():
    """Return unread notification count as JSON for the bell badge."""
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return jsonify({'unread_count': 0})
    target_user_id = session.get('managed_patient_id', session['user_id'])
    conn = get_db_connection()
    row = conn.execute(
        'SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0',
        (target_user_id,)).fetchone()
    conn.close()
    return jsonify({'unread_count': row['cnt'] if row else 0})

@app.route('/api/notifications/clear', methods=['POST'])
def api_notifications_clear():
    """Delete all notifications for the current patient."""
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return jsonify({'status': 'error'}), 401
    target_user_id = session.get('managed_patient_id', session['user_id'])
    conn = get_db_connection()
    conn.execute('DELETE FROM notifications WHERE user_id = ?', (target_user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/patient/appointments')
def patient_appointments():
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return redirect(url_for('index'))
    # Use managed patient if in caretaker mode
    target_user_id = session.get('managed_patient_id', session['user_id'])
    
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT a.*, u.name as doctor_name, u.specialization, u.phone as doctor_phone
        FROM appointments a
        JOIN users u ON a.doctor_id = u.id
        WHERE a.patient_id = ?
        ORDER BY 
            CASE a.status 
                WHEN 'accepted' THEN 1
                WHEN 'pending' THEN 2
                WHEN 'completed' THEN 3
                WHEN 'rejected' THEN 4
                ELSE 5
            END ASC,
            a.appointment_date DESC, a.appointment_time DESC
        LIMIT 4
    ''', (target_user_id,)).fetchall()
    conn.close()
    return render_template('appointments.html', appointments=appointments, active_page='appointments')

@app.route('/patient/lab_reports')
def lab_reports():
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return redirect(url_for('index'))
    # Use managed patient if in caretaker mode
    target_user_id = session.get('managed_patient_id', session['user_id'])
    
    conn = get_db_connection()
    user = conn.execute('SELECT email FROM users WHERE id = ?', (target_user_id,)).fetchone()
    
    if not user:
        conn.close()
        # If user not found, clear session and redirect to login
        session.clear()
        return redirect(url_for('index'))

    uploads = conn.execute(
        'SELECT * FROM lab_uploads WHERE patient_email = ? ORDER BY upload_date DESC LIMIT 2',
        (user['email'],)).fetchall()
    conn.close()
    return render_template('lab_reports.html', uploads=uploads, active_page='reports')

@app.route('/patient/lab_report/download/<path:filename>')
def download_lab_report(filename):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    from flask import send_from_directory
    directory = os.path.abspath(app.config['UPLOAD_FOLDER'])
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/patient/prescriptions')
def prescriptions():
    if 'user_id' not in session or session.get('role') not in ['patient', 'caretaker']:
        return redirect(url_for('index'))
    
    # Use managed patient if in caretaker mode
    target_user_id = session.get('managed_patient_id', session['user_id'])
    
    conn = get_db_connection()
    prescs = conn.execute('''
        SELECT a.*, u.name as doctor_name FROM appointments a
        JOIN users u ON a.doctor_id = u.id
        WHERE a.patient_id = ? AND a.status = 'completed'
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
        LIMIT 2
    ''', (target_user_id,)).fetchall()
    conn.close()
    return render_template('prescriptions.html', prescriptions=prescs, active_page='prescriptions')

# --- Doctor Routes ---
@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    pending = conn.execute('''
        SELECT a.*, u.name as patient_name FROM appointments a 
        JOIN users u ON a.patient_id = u.id 
        WHERE a.doctor_id = ? AND a.status = 'pending'
    ''', (session['user_id'],)).fetchall()
    
    accepted = conn.execute('''
        SELECT a.*, u.name as patient_name FROM appointments a 
        JOIN users u ON a.patient_id = u.id 
        WHERE a.doctor_id = ? AND a.status = 'accepted'
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('doctor_dashboard.html', 
                           pending_appointments=pending, 
                           accepted_appointments=accepted)

@app.route('/doctor/handle_appointment', methods=['POST'])
def handle_appointment():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect(url_for('index'))
    
    appt_id = request.form.get('appointment_id')
    action = request.form.get('action') # 'accept' or 'reject'
    status = 'accepted' if action == 'accept' else 'rejected'
    
    conn = get_db_connection()
    conn.execute('UPDATE appointments SET status = ? WHERE id = ?', (status, appt_id))
    
    # Notify patient (Insert into notifications table)
    appt = conn.execute('SELECT patient_id FROM appointments WHERE id = ?', (appt_id,)).fetchone()
    notif_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('INSERT INTO notifications (user_id, message, type, created_at) VALUES (?, ?, ?, ?)',
                 (appt['patient_id'], f'Your appointment request has been {status} by the doctor.', 'appointment_status', notif_time))
    
    conn.commit()
    conn.close()
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/view_patient_reports/<int:patient_id>')
def view_patient_reports(patient_id):
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    patient = conn.execute('SELECT name, email FROM users WHERE id = ?', (patient_id,)).fetchone()
    if not patient:
        conn.close()
        return "Patient not found", 404
        
    reports = conn.execute(
        'SELECT * FROM lab_uploads WHERE patient_email = ? ORDER BY upload_date DESC LIMIT 1',
        (patient['email'],)).fetchall()
    conn.close()
    
    return render_template('view_patient_reports.html', 
                           patient_name=patient['name'], 
                           reports=reports)

@app.route('/consultation/<int:appt_id>')
def consultation(appt_id):
    if 'user_id' not in session or session['role'] not in ['doctor', 'patient']:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    appt = conn.execute('''
        SELECT a.*, u.name as patient_name FROM appointments a 
        JOIN users u ON a.patient_id = u.id 
        WHERE a.id = ?
    ''', (appt_id,)).fetchone()
    
    if not appt:
        conn.close()
        return "Appointment not found", 404
        
    patient = conn.execute('SELECT * FROM users WHERE id = ?', (appt['patient_id'],)).fetchone()
    
    # Fetch latest health report for AI-generated recommendations
    report = conn.execute('SELECT * FROM health_reports WHERE patient_id = ? ORDER BY report_date DESC', 
                          (appt['patient_id'],)).fetchone()
    
    auto_rec = "No recent health report found for automated recommendations."
    risk_level = "Unknown"
    
    if report:
        risk_level = report['risk_level']
        diseases = report['predicted_diseases'].split(', ')
        auto_rec = f"Based on your {risk_level} status and identified risks:\n\n"
        for d in diseases:
            if 'Diabetes' in d: auto_rec += "• Type 2 Diabetes Management: Prioritize a low-glycemic index diet and consistent HbA1c monitoring.\n"
            elif 'Hypertension' in d: auto_rec += "• Hypertension Protocol: Reduce sodium intake below 2300mg/day and track BP daily.\n"
            elif 'Obesity' in d: auto_rec += "• Weight Management: Aim for a sustainable calorie deficit and 30 mins of moderate activity 5 days/week.\n"
            elif 'Dyslipidemia' in d: auto_rec += "• Lipid Control: Increase dietary fiber and reduce trans fats to improve LDL/HDL ratio.\n"
            elif 'Cardiovascular' in d: auto_rec += "• Heart Health: Focus on Omega-3 rich foods and daily aerobic exercises to strengthen cardiac muscle.\n"
            elif 'Pre-diabetes' in d: auto_rec += "• Pre-Diabetes Reversal: Focus on eliminating processed sugars and increasing physical movement.\n"
        
        if not diseases or 'None' in report['predicted_diseases']:
            auto_rec += "• Maintenance: Continue healthy lifestyle practices and annual screenings to maintain low risk profile.\n"

    conn.close()
    
    # Generate a unique Jitsi room name
    room_name = f"CardioMetabolic_AI_Consult_{appt_id}"
    
    return render_template('consultation.html', 
                           appointment_id=appt_id, 
                           patient=patient,
                           symptoms=appt['symptoms'],
                           risk_level=risk_level,
                           auto_rec=auto_rec,
                           room_name=room_name,
                           role=session['role'])

@app.route('/doctor/save_prescription', methods=['POST'])
def save_prescription():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect(url_for('index'))
    
    appt_id = request.form.get('appointment_id')
    auto_rec = request.form.get('auto_rec', '')
    doctor_notes = request.form.get('doctor_notes', '')
    follow_up = request.form.get('follow_up')
    
    prescription_file = request.files.get('prescription_file')
    filename = 'prescription_record.txt' # Default fallback
    
    if prescription_file and prescription_file.filename != '':
        filename = f"presc_{appt_id}_{prescription_file.filename}"
        prescription_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        # If no file uploaded, we could generate a text file, but for now we'll just keep the default
        # and store the text in the DB.
        pass

    # Combine AI recommendations with doctor's specific clinical notes
    final_prescription = f"{auto_rec}\n\n--- DOCTOR'S CLINICAL NOTES ---\n{doctor_notes}"
    if follow_up:
        final_prescription += f"\n\nFollow-up Date: {follow_up}"

    if filename == 'prescription_record.txt':
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'w') as f:
            f.write(final_prescription)
    
    conn = get_db_connection()
    conn.execute('UPDATE appointments SET status = ?, prescription_path = ?, prescription_text = ? WHERE id = ?', 
                 ('completed', filename, final_prescription, appt_id))
    conn.commit()
    conn.close()
    
    flash('Prescription saved and consultation completed.', 'success')
    return redirect(url_for('doctor_dashboard'))

# --- Caretaker Routes ---
@app.route('/caretaker/dashboard')
def caretaker_dashboard():
    if 'user_id' not in session or session['role'] != 'caretaker':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM users WHERE role = ? AND caretaker_id = ?', 
                            ('patient', session['user_id'])).fetchall()
    conn.close()
    return render_template('caretaker_dashboard.html', patients=patients)

@app.route('/caretaker/view_patient/<int:patient_id>')
def caretaker_view_patient(patient_id):
    if 'user_id' not in session or session['role'] != 'caretaker':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    # Verify caretaker assignment
    patient = conn.execute('SELECT * FROM users WHERE id = ? AND caretaker_id = ?', 
                           (patient_id, session['user_id'])).fetchone()
    conn.close()
    
    if not patient:
        flash("Access denied: Patient not assigned to you.", "danger")
        return redirect(url_for('caretaker_dashboard'))
    
    # Enable "Managed Patient Mode"
    session['managed_patient_id'] = patient_id
    session['managed_patient_name'] = patient['name']
    session['managed_patient_gender'] = patient['gender']
    
    return redirect(url_for('patient_dashboard'))

@app.route('/caretaker/exit_patient_mode')
def exit_patient_mode():
    session.pop('managed_patient_id', None)
    session.pop('managed_patient_name', None)
    session.pop('managed_patient_gender', None)
    return redirect(url_for('caretaker_dashboard'))

# --- Lab Assistant Routes ---
@app.route('/lab_assistant/dashboard')
def lab_assistant_dashboard():
    if 'user_id' not in session or session['role'] != 'lab_assistant':
        return redirect(url_for('index'))
    return render_template('lab_assistant_dashboard.html')

@app.route('/lab_assistant/upload', methods=['POST'])
def lab_upload():
    if 'user_id' not in session or session['role'] != 'lab_assistant':
        return redirect(url_for('index'))
    
    try:
        patient_email = request.form.get('patient_email')
        report_file = request.files.get('report')
        
        if report_file:
            filename = f"lab_{patient_email}_{report_file.filename}"
            report_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            conn = get_db_connection()
            # Find patient id and insert lab_upload record
            patient = conn.execute('SELECT id, age, gender FROM users WHERE email = ?', (patient_email,)).fetchone()
            if patient:
                upload_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                conn.execute(
                    'INSERT INTO lab_uploads (lab_assistant_id, patient_email, file_path, upload_date) VALUES (?, ?, ?, ?)',
                    (session['user_id'], patient_email, filename, upload_time))
                
                # Store filename in type so patient can download the exact file
                notif_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                conn.execute(
                    'INSERT INTO notifications (user_id, message, type, created_at) VALUES (?, ?, ?, ?)',
                    (patient['id'],
                     f'A new lab report "{report_file.filename}" has been uploaded and analyzed for you.',
                     f'report_upload:{filename}',
                     notif_time))
                conn.commit()
            conn.close()
            
            # Automatically analyze the report (simulated) - DONE OUTSIDE OF MAIN CONNECTION TO AVOID LOCKS
            if patient:
                age = patient['age'] if patient['age'] else 35
                gender = 0 if patient['gender'] == 'male' else 1
                report_data = simulate_report_data(age, gender, report_file.filename)
                process_and_save_analysis(patient['id'], report_data)
            
            flash('Report uploaded successfully.', 'success')
        
        return redirect(url_for('lab_assistant_dashboard'))
    except Exception as e:
        return f"<h1>Upload Error:</h1><p>{str(e)}</p>"

@app.route('/seed')
def seed_db():
    try:
        from seed_doctors import seed_doctors
        seed_doctors()
        
        # Seed Lab Assistant
        from database import get_db_connection
        import hashlib
        conn = get_db_connection()
        if conn:
            password = hashlib.sha256('lab123'.encode()).hexdigest()
            try:
                conn.execute('''
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, ?)
                ''', ("Lab Assistant", "lab@example.com", password, "lab_assistant"))
                conn.commit()
            except Exception:
                pass # Already exists
            conn.close()

        return "<h1>Success!</h1><p>Doctors and Lab Assistant have been added to the database.</p>"
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"

if __name__ == '__main__':
    app.run(debug=True)
