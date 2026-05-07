"""
Employee model — CRUD operations for the employees table.
"""

from datetime import datetime
from models.db import get_db_connection


def create_employee(emp_id, name, email, password_hash, dept=None, role='employee'):
    """Insert a new employee record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO employees (empId, name, email, password, role, dept, status, createdAt)
           VALUES (%s, %s, %s, %s, %s, %s, 'Active', %s)""",
        (emp_id, name, email, password_hash, role, dept, datetime.now()),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_employee_by_id(emp_id):
    """Fetch a single employee by empId."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees WHERE empId = %s", (emp_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def get_employee_by_email(email):
    """Fetch a single employee by email."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees WHERE email = %s", (email,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def get_all_employees():
    """Return all employees ordered by creation date."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees ORDER BY createdAt DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def update_employee(emp_id, **kwargs):
    """Update arbitrary fields on an employee row."""
    if not kwargs:
        return
    set_clause = ", ".join(f"{k} = %s" for k in kwargs)
    values = list(kwargs.values()) + [emp_id]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE employees SET {set_clause} WHERE empId = %s", values)
    conn.commit()
    cursor.close()
    conn.close()


def delete_employee(emp_id):
    """Delete an employee record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE empId = %s", (emp_id,))
    conn.commit()
    cursor.close()
    conn.close()
