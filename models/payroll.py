import uuid
from models.db import get_db_connection

class PayrollIntegration:
    def __init__(self, payrollId, userId, baseSalary, deductions, workingDays, month):
        self.payrollId = payrollId
        self.userId = userId
        self.baseSalary = baseSalary
        self.deductions = deductions
        self.workingDays = workingDays
        self.month = month

    @classmethod
    def get_by_user_and_month(cls, userId, month):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM payroll_integration WHERE userId = %s AND month = %s", (userId, month))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return cls(**result)
        return None

    @classmethod
    def create(cls, userId, baseSalary, deductions, workingDays, month):
        payrollId = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payroll_integration (payrollId, userId, baseSalary, deductions, workingDays, month)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (payrollId, userId, baseSalary, deductions, workingDays, month)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return payrollId

    @classmethod
    def update(cls, payrollId, baseSalary, deductions, workingDays):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE payroll_integration 
            SET baseSalary = %s, deductions = %s, workingDays = %s
            WHERE payrollId = %s
            """,
            (baseSalary, deductions, workingDays, payrollId)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
