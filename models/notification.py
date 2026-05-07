"""
Notification model — CRUD operations for the notifications table.
"""

from datetime import datetime
from models.db import get_db_connection


def _generate_notif_id():
    """Generate a unique notification ID like NOT001, NOT002, etc."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notifications")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return f"NOT{count + 1:03d}"


def create_notification(user_id, message, notif_type='Info'):
    """
    Send a notification to a user.

    Parameters
    ----------
    user_id : str
        Target user ID.
    message : str
        Notification message text.
    notif_type : str
        One of 'Info', 'Warning', 'Success', 'Error'.
    """
    notif_id = _generate_notif_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO notifications (notifId, userId, message, type, isRead, sentAt)
           VALUES (%s, %s, %s, %s, FALSE, %s)""",
        (notif_id, str(user_id), message, notif_type, datetime.now()),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return notif_id


def get_notifications_for_user(user_id, unread_only=False, limit=50):
    """Return notifications for a user, optionally filtering to unread only."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM notifications WHERE userId = %s"
    params = [str(user_id)]
    if unread_only:
        query += " AND isRead = FALSE"
    query += " ORDER BY sentAt DESC LIMIT %s"
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_unread_count(user_id):
    """Return the count of unread notifications for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM notifications WHERE userId = %s AND isRead = FALSE",
        (str(user_id),),
    )
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


def mark_as_read(notif_id):
    """Mark a single notification as read."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET isRead = TRUE WHERE notifId = %s", (notif_id,))
    conn.commit()
    cursor.close()
    conn.close()


def mark_all_as_read(user_id):
    """Mark all notifications for a user as read."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notifications SET isRead = TRUE WHERE userId = %s AND isRead = FALSE",
        (str(user_id),),
    )
    conn.commit()
    cursor.close()
    conn.close()


def delete_notification(notif_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notifications WHERE notifId = %s", (notif_id,))
    conn.commit()
    cursor.close()
    conn.close()
