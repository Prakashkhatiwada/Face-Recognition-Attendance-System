"""
Auth routes blueprint — login, signup, logout, forgot password.
"""

from flask import Blueprint, redirect, render_template, request, session, url_for

from models.db import get_db_connection
from services.auth_service import hash_password, verify_password
from models.activity import log_activity

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and verify_password(user['password'], password):
            session['user'] = user['username']
            session['role'] = user.get('role', 'employee')
            
            # Log successful login
            log_activity(user['id'], "Logged in", "Web Login")
            
            if session['role'] == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('attendance.home'))
        else:
            error = "Invalid username or password"

    return render_template('adminlogin.html', error=error)


@auth_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and verify_password(user['password'], password):
            session['user'] = user['username']
            session['role'] = user.get('role', 'employee')
            
            # Log successful admin login
            log_activity(user['id'], "Admin logged in", "Admin Portal")
            
            if session['role'] == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('attendance.home'))
        else:
            error = 'Invalid credentials'

    return render_template('adminlogin.html', error=error)


@auth_bp.route('/logout')
def logout():
    username = session.get('user')
    if username:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row:
            log_activity(row[0], "Logged out", "Web")
        cursor.close()
        conn.close()
    
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/sign', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email'].lower()
        password = request.form['password']
        role = request.form.get('role', 'employee')

        if not username or not email or not password:
            return render_template('sign.html', error="All fields are required")

        hashed = hash_password(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                (username, email, hashed, role),
            )
            conn.commit()
        except Exception as e:
            print("DB Insert Error:", e)
            return render_template('sign.html', error="User already exists or invalid data")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('auth.login'))

    return render_template('sign.html')


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        return render_template('forgot_success.html', email=email)
    return render_template('forgot_password.html')
