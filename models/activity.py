"""
Activity model — CRUD operations for the activities table.
Provides an audit trail for all significant user actions.
"""

from datetime import datetime
from models.db import get_db_connection


def _generate_activity_id():
    """Generate a unique activity ID like ACT001, ACT002, etc."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM activities")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return f"ACT{count + 1:03d}"


def log_activity(user_id, action, location=None):
    """
    Record a user action in the activity log.

    Parameters
    ----------
    user_id : str
        The ID of the user performing the action.
    action : str
        Description of the action, e.g. "Logged in", "Marked attendance".
    location : str, optional
        Physical or logical location, e.g. "Main Office", "Admin Panel".
    """
    act_id = _generate_activity_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO activities (actId, userId, action, location, timestamp)
           VALUES (%s, %s, %s, %s, %s)""",
        (act_id, str(user_id), action, location, datetime.now()),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return act_id


def get_activities_by_user(user_id, limit=50):
    """Return recent activities for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT * FROM activities
           WHERE userId = %s
           ORDER BY timestamp DESC
           LIMIT %s""",
        (str(user_id), limit),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_all_activities(limit=100):
    """Return the most recent activities across all users."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM activities ORDER BY timestamp DESC LIMIT %s",
        (limit,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_activities_by_date(target_date=None, limit=100):
    """Return all activities for a specific date."""
    target_date = target_date or datetime.today().date()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT * FROM activities
           WHERE DATE(timestamp) = %s
           ORDER BY timestamp DESC
           LIMIT %s""",
        (target_date, limit),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
