"""
FaceData model — CRUD operations for the face_data table.
"""

import json
from datetime import datetime
from models.db import get_db_connection


def create_face_data(face_id, user_id, encoding=None, image_count=0):
    """Store a face encoding record for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO face_data (faceId, userId, encoding, imageCount, isActive, capturedAt)
           VALUES (%s, %s, %s, %s, TRUE, %s)""",
        (face_id, user_id, json.dumps(encoding) if encoding else None, image_count, datetime.now()),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_face_data_by_user(user_id):
    """Return all face data entries for a given user."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM face_data WHERE userId = %s AND isActive = TRUE", (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def update_face_data(face_id, **kwargs):
    if not kwargs:
        return
    set_clause = ", ".join(f"{k} = %s" for k in kwargs)
    values = list(kwargs.values()) + [face_id]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE face_data SET {set_clause} WHERE faceId = %s", values)
    conn.commit()
    cursor.close()
    conn.close()


def deactivate_face_data(user_id):
    """Mark all face data for a user as inactive (soft delete)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE face_data SET isActive = FALSE WHERE userId = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()


def delete_face_data(face_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM face_data WHERE faceId = %s", (face_id,))
    conn.commit()
    cursor.close()
    conn.close()
