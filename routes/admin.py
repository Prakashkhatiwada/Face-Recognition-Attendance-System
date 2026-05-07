"""
Admin routes blueprint — dashboard, user management, system controls.
"""

import os
import shutil
from datetime import datetime

from flask import Blueprint, redirect, render_template, request, session, url_for, jsonify
import cv2
import numpy as np
from PIL import Image

from models.db import get_db_connection
from services.auth_service import hash_password
from services.face_service import extract_faces, train_model
from services.notification_service import notify_account_created
from models.activity import log_activity
from models.system_report import SystemReport
from models.payroll import PayrollIntegration
from services.report_service import generate_system_report, calculate_payroll
from utils.decorators import admin_required
import config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')




@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    today = datetime.now().date()
    
    # Total Employees
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role != 'admin'")
    total_employees = cursor.fetchone()['count']
    
    # Present Today
    cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE date = %s AND status = 'present'", (today,))
    present_today = cursor.fetchone()['count']
    
    # Late Today (assuming 10:05 is late)
    cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE date = %s AND TIME(check_in) > '10:05:00'", (today,))
    late_today = cursor.fetchone()['count']
    
    # Absent Today
    absent_today = max(0, total_employees - present_today)

    # Recent Activity (Last 5 records)
    cursor.execute("""
        SELECT u.username, a.check_in, a.status 
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.check_in DESC
        LIMIT 5
    """)
    recent_activity = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin.html', 
                          total_employees=total_employees,
                          present_today=present_today,
                          late_today=late_today,
                          absent_today=absent_today,
                          recent_activity=recent_activity)




@admin_bp.route('/reset_system', methods=['POST'])
@admin_required
def reset_system():
    # 1. Delete all face data
    if os.path.exists(config.FACES_DIR):
        shutil.rmtree(config.FACES_DIR)
    os.makedirs(config.FACES_DIR, exist_ok=True)
    os.makedirs(os.path.join(config.FACES_DIR, 'full_time'), exist_ok=True)
    os.makedirs(os.path.join(config.FACES_DIR, 'part_time'), exist_ok=True)

    # 2. Delete model
    if os.path.exists(config.MODEL_PATH):
        os.remove(config.MODEL_PATH)

    # 3. Clear attendance logs
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE attendance")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error resetting DB:", e)

    admin_id = session.get('user_id') or 0 # Fallback if no ID in session
    log_activity(admin_id, "Reset system data (deleted all models and attendance)", "Admin Portal")

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/retrain', methods=['POST'])
@admin_required
def retrain():
    train_model()
    admin_id = session.get('user_id') or 0
    log_activity(admin_id, "Manually retrained recognition model", "Admin Portal")
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/delete_user/<username>', methods=['POST'])
@admin_required
def delete_user(username):
    username = username.strip()

    # 1. Delete face image folders
    if os.path.exists(config.FACES_DIR):
        for emp_type in os.listdir(config.FACES_DIR):
            emp_dir = os.path.join(config.FACES_DIR, emp_type)
            if not os.path.isdir(emp_dir):
                continue
            for d in os.listdir(emp_dir):
                if d.startswith(username + '_'):
                    user_folder = os.path.join(emp_dir, d)
                    try:
                        shutil.rmtree(user_folder)
                        print(f"Deleted folder: {user_folder}")
                    except Exception as e:
                        print(f"Error deleting folder {user_folder}: {e}")

    # 2. Retrain model
    train_model()

    # 3. Delete from DB
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, role FROM users WHERE username = %s", (username,))
        user_row = cursor.fetchone()

        if user_row:
            user_id, user_role = user_row[0], user_row[1]

            # Prevent admin deletion
            if user_role == 'admin':
                print(f"Deletion aborted: {username} is an admin.")
                cursor.close()
                conn.close()
                return redirect(url_for('admin.admin_dashboard'))

            cursor.execute("DELETE FROM attendance WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            print(f"Deleted user {username} (ID: {user_id}) and their attendance.")
            
            admin_id = session.get('user_id') or 0
            log_activity(admin_id, f"Deleted user {username}", "Admin Portal")
        else:
            print(f"User {username} not found in DB.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error deleting user {username} from DB: {e}")

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/add_user_init', methods=['POST'])
@admin_required
def add_user_init():
    newusername = request.form.get('newusername', '').strip()
    newuserid = request.form.get('newuserid', '').strip()
    newuserrole = request.form.get('role', 'employee')

    if not newusername or not newuserid:
        return redirect(url_for('admin.admin_dashboard'))

    session['add_username'] = newusername
    session['add_userid'] = newuserid
    session['add_role'] = newuserrole

    folder_name = 'part_time' if newuserrole == 'part_time' else 'full_time'
    userimagefolder = os.path.join(config.FACES_DIR, folder_name, f'{newusername}_{newuserid}')
    os.makedirs(userimagefolder, exist_ok=True)

    return render_template('add_user_capture.html', username=newusername, userid=newuserid)


@admin_bp.route('/capture_with_upload', methods=['POST'])
def capture_with_upload():
    """Called by add_user_capture.html via AJAX to save one frame."""
    if 'add_username' not in session:
        return jsonify(success=False, message="Session expired. Please restart."), 403

    username = session['add_username']
    userid = session['add_userid']
    role = session.get('add_role', 'employee')
    folder_name = 'part_time' if role == 'part_time' else 'full_time'
    userimagefolder = os.path.join(config.FACES_DIR, folder_name, f'{username}_{userid}')

    if 'image' not in request.files:
        return jsonify(success=False, message="No image received"), 400

    file = request.files['image']
    try:
        img = Image.open(file.stream).convert('RGB')
        frame = np.array(img)[:, :, ::-1]  # RGB -> BGR

        faces = extract_faces(frame)
        if len(faces) == 0:
            return jsonify(success=False, message="No face detected. Try again."), 200

        (x, y, w, h) = faces[0]
        face_img = frame[y:y+h, x:x+w]

        timestamp = datetime.now().strftime("%H%M%S_%f")
        filename = f"{username}_{userid}_{timestamp}.jpg"
        save_path = os.path.join(userimagefolder, filename)

        cv2.imwrite(save_path, face_img)
        return jsonify(success=True, message="Captured"), 200

    except Exception as e:
        print(f"Capture error: {e}")
        return jsonify(success=False, message="Server error processing image"), 500


@admin_bp.route('/end_capture', methods=['POST'])
@admin_required
def end_capture():
    train_model()

    newusername = session.get('add_username')
    newuserrole = session.get('add_role', 'employee')

    if newusername:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE username = %s OR id = %s",
                (newusername, session['add_userid']),
            )
            if not cursor.fetchone():
                hashed = hash_password('changeme')
                cursor.execute(
                    "INSERT INTO users (id, username, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                    (session['add_userid'], newusername, f'{newusername}@example.com', hashed, newuserrole),
                )
                conn.commit()
                
                # Notifications and activity
                notify_account_created(session['add_userid'], newusername)
                admin_id = session.get('user_id') or 0
                log_activity(admin_id, f"Created new user {newusername}", "Admin Portal")
                
            cursor.close()
            conn.close()
        except Exception as e:
            print('DB add user error:', e)

    session.pop('add_username', None)
    session.pop('add_userid', None)
    session.pop('add_role', None)

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/add', methods=['POST'])
@admin_required
def add():
    """Legacy add-user route using server-side webcam (cv2.VideoCapture)."""
    newusername = request.form.get('newusername', '').strip()
    newuserid = request.form.get('newuserid', '').strip()
    newuserrole = request.form.get('role', 'employee')

    try:
        newuserid_int = int(newuserid)
        if not newusername or not newuserid or newuserid_int < 1:
            return redirect(url_for('admin.admin_dashboard'))
    except ValueError:
        return redirect(url_for('admin.admin_dashboard'))

    folder_name = 'part_time' if newuserrole == 'part_time' else 'full_time'
    userimagefolder = os.path.join(config.FACES_DIR, folder_name, f'{newusername}_{newuserid}')
    os.makedirs(userimagefolder, exist_ok=True)

    cap_local = cv2.VideoCapture(0)
    i, j = 0, 0
    while True:
        ret, frame = cap_local.read()
        if not ret:
            break
        faces = extract_faces(frame)
        for (x, y, w, h) in faces:
            if j % 10 == 0:
                name = f'{newusername}_{i}.jpg'
                cv2.imwrite(os.path.join(userimagefolder, name), frame[y:y+h, x:x+w])
                i += 1
            j += 1
        if j >= 500 or cv2.waitKey(1) == 27:
            break
    cap_local.release()
    cv2.destroyAllWindows()
    train_model()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR id = %s",
            (newusername, newuserid),
        )
        if not cursor.fetchone():
            hashed = hash_password('changeme')
            cursor.execute(
                "INSERT INTO users (id, username, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                (newuserid, newusername, f'{newusername}@example.com', hashed, newuserrole),
            )
            conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print('DB add user error (non-fatal):', e)

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/reports')
@admin_required
def system_reports():
    reports = SystemReport.get_all()
    return render_template('admin_reports.html', reports=reports)

@admin_bp.route('/reports/generate', methods=['POST'])
@admin_required
def generate_report():
    period = request.form.get('period') # format YYYY-MM
    admin_id = session.get('user_id') or 'admin'
    if period:
        generate_system_report(period, admin_id)
        log_activity(admin_id, f"Generated system report for {period}", "Admin Portal")
    return redirect(url_for('admin.system_reports'))

@admin_bp.route('/payroll')
@admin_required
def payroll_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Fetch all employees
    cursor.execute("SELECT id, username FROM users WHERE role != 'admin'")
    employees = cursor.fetchall()
    
    # Fetch all payroll records
    cursor.execute("SELECT * FROM payroll_integration ORDER BY month DESC")
    payrolls = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('admin_payroll.html', employees=employees, payrolls=payrolls)

@admin_bp.route('/payroll/calculate', methods=['POST'])
@admin_required
def calculate_employee_payroll():
    user_id = request.form.get('user_id')
    month = request.form.get('month')
    base_salary = float(request.form.get('base_salary', 0))
    
    if user_id and month and base_salary:
        calculate_payroll(user_id, month, base_salary)
        admin_id = session.get('user_id') or 'admin'
        log_activity(admin_id, f"Calculated payroll for user {user_id} for {month}", "Admin Portal")
        
    return redirect(url_for('admin.payroll_dashboard'))


@admin_bp.route('/attendance')
@admin_required
def attendance_log():
    """Show per-employee day-by-day attendance for a selected month."""
    import calendar
    period = request.args.get('period', datetime.now().strftime('%Y-%m'))
    year, month = period.split('-')
    year, month = int(year), int(month)
    days_in_month = calendar.monthrange(year, month)[1]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get ALL users (including admin)
    cursor.execute("SELECT id, username, role FROM users ORDER BY id")
    users = cursor.fetchall()

    # Get all attendance records for the period
    cursor.execute(
        """
        SELECT user_id, date, status, check_in, check_out
        FROM attendance
        WHERE YEAR(date) = %s AND MONTH(date) = %s
        ORDER BY date
        """,
        (year, month)
    )
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    # Build a lookup: { user_id: { day_number: record } }
    att_map = {}
    for r in records:
        uid = r['user_id']
        day = r['date'].day
        if uid not in att_map:
            att_map[uid] = {}
        att_map[uid][day] = r

    # Build employee data list
    employees = []
    for u in users:
        days = []
        present_count = 0
        absent_count = 0
        for d in range(1, days_in_month + 1):
            rec = att_map.get(u['id'], {}).get(d)
            if rec:
                status = rec['status']
                if status == 'present':
                    present_count += 1
                elif status == 'absent':
                    absent_count += 1
                days.append({'day': d, 'status': status, 'check_in': rec.get('check_in'), 'check_out': rec.get('check_out')})
            else:
                days.append({'day': d, 'status': None})
        employees.append({
            'id': u['id'],
            'username': u['username'],
            'role': u['role'],
            'days': days,
            'present': present_count,
            'absent': absent_count,
        })

    return render_template(
        'admin_attendance.html',
        employees=employees,
        period=period,
        days_in_month=days_in_month,
        year=year,
        month=month,
    )


@admin_bp.route('/search_employee')
@admin_required
def search_employee():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    today = datetime.now().date()
    
    # Search users and join with today's attendance
    cursor.execute("""
        SELECT u.id, u.username, u.role, a.status, a.check_in, a.check_out
        FROM users u
        LEFT JOIN attendance a ON u.id = a.user_id AND a.date = %s
        WHERE u.username LIKE %s AND u.role != 'admin'
        LIMIT 10
    """, (today, f'%{query}%'))
    
    results = cursor.fetchall()
    
    # Format objects for JSON
    for r in results:
        if r['check_in'] and hasattr(r['check_in'], 'strftime'):
            r['check_in'] = r['check_in'].strftime('%I:%M %p')
        elif r['check_in']:
            r['check_in'] = str(r['check_in'])
            
        if r['check_out'] and hasattr(r['check_out'], 'strftime'):
            r['check_out'] = r['check_out'].strftime('%I:%M %p')
        elif r['check_out']:
            r['check_out'] = str(r['check_out'])
            
    cursor.close()
    conn.close()
    return jsonify(results)
