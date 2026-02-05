import sqlite3
from datetime import datetime

DB_NAME = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Table to link ID -> Name
    cursor.execute('''CREATE TABLE IF NOT EXISTS registry 
                      (device_id TEXT PRIMARY KEY, roll_no TEXT, name TEXT)''')
    # Table for logs
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance_logs 
                      (id INTEGER PRIMARY KEY, roll_no TEXT, name TEXT, 
                       timestamp DATETIME, status TEXT)''')
    conn.commit()
    conn.close()

def register_student(device_id, roll_no, name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO registry (device_id, roll_no, name) VALUES (?, ?, ?)", 
                   (device_id, roll_no, name))
    conn.commit()
    conn.close()
    print(f"💾 Saved: {name} ({roll_no}) -> ID: {device_id}")

def get_student_identity(device_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT roll_no, name FROM registry WHERE device_id = ?", (device_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def mark_attendance(roll_no, name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Log the time
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO attendance_logs (roll_no, name, timestamp, status) VALUES (?, ?, ?, ?)",
                   (roll_no, name, time_now, "PRESENT"))
    conn.commit()
    conn.close()

# Run once to create file
if __name__ == "__main__":
    init_db()