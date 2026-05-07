import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "12345",    
    "database": "attendance_system"
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("--- users table ---")
    cursor.execute("DESCRIBE users")
    for column in cursor.fetchall():
        print(column)
        
    print("\n--- attendance table ---")
    cursor.execute("DESCRIBE attendance")
    for column in cursor.fetchall():
        print(column)
        
    cursor.close()
    conn.close()
except mysql.connector.Error as err:
    print(f"Error: {err}")
