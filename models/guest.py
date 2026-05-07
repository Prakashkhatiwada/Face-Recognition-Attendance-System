"""
Guest model — CRUD operations for the guests table.
"""

from datetime import datetime
from models.db import get_db_connection


def create_guest(guest_id, name, email=None):
    """Register a new guest."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO guests (guestId, name, email, role, status, registeredAt)
           VALUES (%s, %s, %s, 'guest', 'Pending', %s)""",
        (guest_id, name, email, datetime.now()),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_guest_by_id(guest_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM guests WHERE guestId = %s", (guest_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def get_all_guests():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM guests ORDER BY registeredAt DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def update_guest_status(guest_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE guests SET status = %s WHERE guestId = %s", (status, guest_id))
    conn.commit()
    cursor.close()
    conn.close()


def delete_guest(guest_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guests WHERE guestId = %s", (guest_id,))
    conn.commit()
    cursor.close()
    conn.close()
