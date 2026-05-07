"""
Attendance Service — check-in / check-out business logic.

Uses the LEGACY ``users`` + ``attendance`` tables during Phase-1 so existing
data keeps working.  After full migration the helpers can switch to the new
schema transparently.
"""

from datetime import datetime

from models.db import get_db_connection
from models.activity import log_activity
from services.notification_service import notify_attendance_marked
import config


def extract_attendance_from_db():
    """
    Return ``(names, rolls, times, length)`` for today's attendance using the
    legacy ``users`` + ``attendance`` tables.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
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

    names, rolls, times = [], [], []
    for r in rows:
        names.append(r[0])
        rolls.append(str(r[1]))
        check_in = r[2].strftime('%H:%M:%S') if r[2] else ''
        if r[3]:
            check_out = r[3].strftime('%H:%M:%S')
            times.append(f'In:{check_in} Out:{check_out}')
        else:
            times.append(f'In:{check_in}')
    return names, rolls, times, len(names)


def add_attendance_db(label):
    """
    Parse a label of the form ``username_userid`` and record check-in or
    check-out in the legacy attendance table.

    Returns one of:
      ``'check-in'``, ``'check-out'``, ``'already_done'``,
      ``'time_restricted_in'``, ``'time_restricted_out'``
    """
    try:
        username, userid = label.rsplit('_', 1)
        userid = int(userid)
    except Exception:
        return False

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    today = datetime.today().date()

    # 1. Get user role
    cursor.execute("SELECT role FROM users WHERE id = %s", (userid,))
    user_row = cursor.fetchone()
    user_role = user_row['role'] if user_row and user_row.get('role') else 'employee'

    # 2. Check existing record
    cursor.execute(
        "SELECT * FROM attendance WHERE user_id = %s AND date = %s",
        (userid, today),
    )
    row = cursor.fetchone()
    now = datetime.now()
    current_hour = now.hour

    if not row:
        # ── CHECK-IN ──
        allowed = (user_role == 'part_time') or (config.CHECK_IN_START <= current_hour < config.CHECK_IN_END)
        if allowed:
            cursor.execute(
                "INSERT INTO attendance (user_id, check_in, date, status) VALUES (%s, %s, %s, %s)",
                (userid, now, today, 'present'),
            )
            conn.commit()
            
            log_activity(userid, "Checked In", "Camera Kiosk")
            notify_attendance_marked(userid, username, 'check-in')
            
            cursor.close(); conn.close()
            return 'check-in'
        
        notify_attendance_marked(userid, username, 'time_restricted_in')
        cursor.close(); conn.close()
        return 'time_restricted_in'
    else:
        if row.get('check_out') is None:
            # ── CHECK-OUT ──
            allowed = (user_role == 'part_time') or (config.CHECK_OUT_START <= current_hour < config.CHECK_OUT_END)
            if allowed:
                cursor.execute(
                    "UPDATE attendance SET check_out = %s WHERE id = %s",
                    (now, row['id']),
                )
                conn.commit()
                
                log_activity(userid, "Checked Out", "Camera Kiosk")
                notify_attendance_marked(userid, username, 'check-out')
                
                cursor.close(); conn.close()
                return 'check-out'
                
            notify_attendance_marked(userid, username, 'time_restricted_out')
            cursor.close(); conn.close()
            return 'time_restricted_out'
        else:
            cursor.close(); conn.close()
            return 'already_done'
