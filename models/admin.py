"""
Admin model — CRUD operations for the admins table.
"""

from datetime import datetime
from models.db import get_db_connection


def create_admin(admin_id, name, email, password_hash, dept=None):
    """Insert a new admin record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO admins (adminId, name, email, password, role, dept, status, createdAt)
           VALUES (%s, %s, %s, %s, 'admin', %s, 'Active', %s)""",
        (admin_id, name, email, password_hash, dept, datetime.now()),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_admin_by_id(admin_id):
    """Fetch a single admin by adminId."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admins WHERE adminId = %s", (admin_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def get_admin_by_email(email):
    """Fetch a single admin by email."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def get_all_admins():
    """Return a list of all admin records."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admins ORDER BY createdAt DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def update_admin_status(admin_id, status):
    """Update the status field (Active / Inactive)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE admins SET status = %s WHERE adminId = %s", (status, admin_id))
    conn.commit()
    cursor.close()
    conn.close()


def delete_admin(admin_id):
    """Delete an admin record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE adminId = %s", (admin_id,))
    conn.commit()
    cursor.close()
    conn.close()
