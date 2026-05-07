import uuid
from datetime import datetime
from models.db import get_db_connection

class AttendanceSummary:
    def __init__(self, summaryId, userId, totalPresent, totalAbsent, totalHours, period):
        self.summaryId = summaryId
        self.userId = userId
        self.totalPresent = totalPresent
        self.totalAbsent = totalAbsent
        self.totalHours = totalHours
        self.period = period

    @classmethod
    def get_by_user_and_period(cls, userId, period):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM attendance_summary WHERE userId = %s AND period = %s", (userId, period))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return cls(**result)
        return None

    @classmethod
    def create(cls, userId, totalPresent, totalAbsent, totalHours, period):
        summaryId = f"SUM-{uuid.uuid4().hex[:8].upper()}"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO attendance_summary (summaryId, userId, totalPresent, totalAbsent, totalHours, period)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (summaryId, userId, totalPresent, totalAbsent, totalHours, period)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return summaryId

    @classmethod
    def update(cls, summaryId, totalPresent, totalAbsent, totalHours):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE attendance_summary 
            SET totalPresent = %s, totalAbsent = %s, totalHours = %s
            WHERE summaryId = %s
            """,
            (totalPresent, totalAbsent, totalHours, summaryId)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
