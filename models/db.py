"""
Database connection helper and schema initialisation.

Calling ``init_db()`` will create every table that does not yet exist so the
application can start cleanly on a fresh MySQL instance.
"""

import mysql.connector
from config import DB_CONFIG


def get_db_connection():
    """Return a new MySQL connection using the app-wide config."""
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Create all tables if they do not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # ── Phase 1 tables ────────────────────────────────────────

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            adminId   VARCHAR(20) PRIMARY KEY,
            name      VARCHAR(100) NOT NULL,
            email     VARCHAR(120) UNIQUE NOT NULL,
            password  VARCHAR(255) NOT NULL,
            role      VARCHAR(20)  DEFAULT 'admin',
            dept      VARCHAR(50),
            status    VARCHAR(20)  DEFAULT 'Active',
            createdAt DATETIME     DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            empId     VARCHAR(20) PRIMARY KEY,
            name      VARCHAR(100) NOT NULL,
            email     VARCHAR(120) UNIQUE NOT NULL,
            password  VARCHAR(255) NOT NULL,
            role      VARCHAR(20)  DEFAULT 'employee',
            dept      VARCHAR(50),
            status    VARCHAR(20)  DEFAULT 'Active',
            createdAt DATETIME     DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            guestId      VARCHAR(20) PRIMARY KEY,
            name         VARCHAR(100) NOT NULL,
            email        VARCHAR(120),
            role         VARCHAR(20)  DEFAULT 'guest',
            status       VARCHAR(20)  DEFAULT 'Pending',
            registeredAt DATETIME     DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS face_data (
            faceId     VARCHAR(20) PRIMARY KEY,
            userId     VARCHAR(20) NOT NULL,
            encoding   JSON,
            imageCount INT          DEFAULT 0,
            isActive   BOOLEAN      DEFAULT TRUE,
            capturedAt DATETIME     DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            attendId  INT AUTO_INCREMENT PRIMARY KEY,
            userId    VARCHAR(20) NOT NULL,
            date      DATE        NOT NULL,
            checkIn   DATETIME,
            checkOut  DATETIME,
            status    VARCHAR(20) DEFAULT 'Present'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS face_recognition_engine (
            engineId      VARCHAR(20) PRIMARY KEY,
            modelPath     VARCHAR(255),
            threshold     FLOAT        DEFAULT 0.6,
            frameRate     INT          DEFAULT 30,
            isRunning     BOOLEAN      DEFAULT TRUE,
            lastRetrained DATETIME
        )
    """)

    # ── Phase 2 tables ────────────────────────────────────────

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            tokenId   VARCHAR(20) PRIMARY KEY,
            userId    VARCHAR(20) NOT NULL,
            token     TEXT         NOT NULL,
            expiresAt DATETIME     NOT NULL,
            revoked   BOOLEAN      DEFAULT FALSE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            actId     VARCHAR(20) PRIMARY KEY,
            userId    VARCHAR(20) NOT NULL,
            action    VARCHAR(255),
            location  VARCHAR(100),
            timestamp DATETIME     DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            notifId  VARCHAR(20) PRIMARY KEY,
            userId   VARCHAR(20) NOT NULL,
            message  TEXT,
            type     VARCHAR(20) DEFAULT 'Info',
            isRead   BOOLEAN     DEFAULT FALSE,
            sentAt   DATETIME    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Phase 3 tables ────────────────────────────────────────

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_summary (
            summaryId    VARCHAR(20) PRIMARY KEY,
            userId       VARCHAR(20) NOT NULL,
            totalPresent INT          DEFAULT 0,
            totalAbsent  INT          DEFAULT 0,
            totalHours   FLOAT        DEFAULT 0,
            period       VARCHAR(20)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_reports (
            reportId    VARCHAR(20) PRIMARY KEY,
            period      VARCHAR(20),
            totalPresent INT DEFAULT 0,
            totalAbsent  INT DEFAULT 0,
            totalLate    INT DEFAULT 0,
            generatedBy  VARCHAR(20),
            createdAt    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payroll_integration (
            payrollId  VARCHAR(20) PRIMARY KEY,
            userId     VARCHAR(20) NOT NULL,
            baseSalary FLOAT        DEFAULT 0,
            deductions FLOAT        DEFAULT 0,
            workingDays INT         DEFAULT 0,
            month      VARCHAR(20)
        )
    """)

    # ── Keep legacy users table for backward compatibility ────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email    VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role     VARCHAR(20)  DEFAULT 'employee'
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✔ Database initialised — all tables ready.")
