"""
Attendance model — CRUD operations for the attendance table.

Note: This module talks to the NEW ``attendance`` schema (attendId, userId
as VARCHAR, etc.).  The legacy ``attendance`` table (with integer user_id
and foreign key to ``users``) is still used by the services layer during
the Phase-1 transition; once migration is complete this model will become
the single source of truth.
"""

from datetime import datetime, date as date_type
from models.db import get_db_connection


# ── Legacy helpers (keep the old table working during Phase 1) ────

def get_today_attendance_legacy():
    """Query the LEGACY attendance + users table (Phase-1 compat)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    today = datetime.today().date()
    cursor.execute(
        """
        SELECT u.username, u.id, a.check_in, a.check_out, a.status
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        WHERE a.date = %s
        ORDER BY a.check_in ASC
        """,
        (today,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ── New-schema helpers ────────────────────────────────────────────

def create_attendance(user_id, check_in=None, status='Present'):
    """Insert a new attendance record for today."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO attendance (userId, date, checkIn, checkOut, status)
           VALUES (%s, %s, %s, NULL, %s)""",
        (user_id, datetime.today().date(), check_in or datetime.now(), status),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_attendance_by_user_today(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    today = datetime.today().date()
    cursor.execute(
        "SELECT * FROM attendance WHERE userId = %s AND date = %s",
        (user_id, today),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def update_checkout(attend_id, check_out=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE attendance SET checkOut = %s WHERE attendId = %s",
        (check_out or datetime.now(), attend_id),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_attendance_by_date(target_date=None):
    """Return all attendance rows for a given date (defaults to today)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    target_date = target_date or datetime.today().date()
    cursor.execute("SELECT * FROM attendance WHERE date = %s ORDER BY checkIn ASC", (target_date,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def truncate_attendance():
    """Remove all attendance records (admin reset)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE attendance")
    conn.commit()
    cursor.close()
    conn.close()
