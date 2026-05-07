import uuid
from datetime import datetime
from models.db import get_db_connection

class SystemReport:
    def __init__(self, reportId, period, totalPresent, totalAbsent, totalLate, generatedBy, createdAt):
        self.reportId = reportId
        self.period = period
        self.totalPresent = totalPresent
        self.totalAbsent = totalAbsent
        self.totalLate = totalLate
        self.generatedBy = generatedBy
        self.createdAt = createdAt

    @classmethod
    def get_all(cls):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM system_reports ORDER BY createdAt DESC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [cls(**r) for r in results]

    @classmethod
    def create(cls, period, totalPresent, totalAbsent, totalLate, generatedBy):
        reportId = f"REP-{uuid.uuid4().hex[:8].upper()}"
        createdAt = datetime.now()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO system_reports (reportId, period, totalPresent, totalAbsent, totalLate, generatedBy, createdAt)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (reportId, period, totalPresent, totalAbsent, totalLate, generatedBy, createdAt)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return reportId
