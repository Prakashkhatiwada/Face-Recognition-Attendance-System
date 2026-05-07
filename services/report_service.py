from datetime import datetime
from models.db import get_db_connection
from models.attendance_summary import AttendanceSummary
from models.system_report import SystemReport
from models.payroll import PayrollIntegration

def calculate_attendance_summary(user_id, period):
    # period format: 'YYYY-MM'
    year, month = period.split('-')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Calculate totals
    cursor.execute(
        """
        SELECT 
            COUNT(CASE WHEN status = 'present' THEN 1 END) as totalPresent,
            COUNT(CASE WHEN status = 'absent' THEN 1 END) as totalAbsent
        FROM attendance 
        WHERE user_id = %s AND YEAR(date) = %s AND MONTH(date) = %s
        """,
        (user_id, year, month)
    )
    result = cursor.fetchone()
    
    # Calculate hours (simplified, assuming 8 hours per present day for now if no checkout, or diff if checkout)
    cursor.execute(
        """
        SELECT check_in as checkIn, check_out as checkOut
        FROM attendance
        WHERE user_id = %s AND YEAR(date) = %s AND MONTH(date) = %s AND status = 'present'
        """,
        (user_id, year, month)
    )
    attendance_records = cursor.fetchall()
    
    total_hours = 0
    for record in attendance_records:
        if record['checkIn'] and record['checkOut']:
            delta = record['checkOut'] - record['checkIn']
            total_hours += delta.total_seconds() / 3600
        else:
            # Default to 8 hours if no checkout but marked present
            total_hours += 8
            
    cursor.close()
    conn.close()
    
    total_present = result['totalPresent'] or 0
    total_absent = result['totalAbsent'] or 0
    
    existing_summary = AttendanceSummary.get_by_user_and_period(user_id, period)
    if existing_summary:
        AttendanceSummary.update(existing_summary.summaryId, total_present, total_absent, total_hours)
        return existing_summary.summaryId
    else:
        return AttendanceSummary.create(user_id, total_present, total_absent, total_hours, period)

def generate_system_report(period, admin_id):
    year, month = period.split('-')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        """
        SELECT 
            COUNT(CASE WHEN status = 'present' THEN 1 END) as totalPresent,
            COUNT(CASE WHEN status = 'absent' THEN 1 END) as totalAbsent,
            COUNT(CASE WHEN status = 'late' THEN 1 END) as totalLate
        FROM attendance 
        WHERE YEAR(date) = %s AND MONTH(date) = %s
        """,
        (year, month)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    total_present = result['totalPresent'] or 0
    total_absent = result['totalAbsent'] or 0
    total_late = result['totalLate'] or 0
    
    return SystemReport.create(period, total_present, total_absent, total_late, admin_id)

def calculate_payroll(user_id, month, base_salary):
    # Ensure attendance summary exists for accurate calculation
    summary_id = calculate_attendance_summary(user_id, month)
    summary = AttendanceSummary.get_by_user_and_period(user_id, month)
    
    working_days = summary.totalPresent
    
    # Simplified deduction calculation: assuming 22 working days in a month.
    # Deduct proportionally for days absent.
    daily_rate = base_salary / 22
    deductions = summary.totalAbsent * daily_rate
    
    existing_payroll = PayrollIntegration.get_by_user_and_month(user_id, month)
    if existing_payroll:
        PayrollIntegration.update(existing_payroll.payrollId, baseSalary=base_salary, deductions=deductions, workingDays=working_days)
        return existing_payroll.payrollId
    else:
        return PayrollIntegration.create(user_id, base_salary, deductions, working_days, month)
