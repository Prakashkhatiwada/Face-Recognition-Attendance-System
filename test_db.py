import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "00000",    
    "database": "attendance_system"
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    print("Connection successful!")
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("Tables in database:", tables)
    cursor.close()
    conn.close()
except mysql.connector.Error as err:
    print(f"Error: {err}")
