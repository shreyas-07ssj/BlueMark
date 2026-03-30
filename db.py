import sqlite3
import csv
import os
from datetime import datetime

# ---------------------------------------------------------
# FIX 1: ABSOLUTE PATH
# This guarantees the database is ALWAYS created in the 
# exact same folder as this db.py script, preventing the 
# "no such table" error regardless of where you run it from.
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "attendance.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Master Students Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                      (roll_no TEXT PRIMARY KEY, 
                       name TEXT, 
                       class_name TEXT, 
                       device_id TEXT UNIQUE)''')
    
    # 2. Daily Attendance Logs
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance_logs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       roll_no TEXT, 
                       date TEXT, 
                       in_time TEXT, 
                       last_seen TEXT,
                       scan_method TEXT,
                       session_id TEXT)''')
    conn.commit()
    conn.close()

def add_or_edit_student(roll_no, name, class_name, device_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO students (roll_no, name, class_name, device_id) 
                      VALUES (?, ?, ?, ?)
                      ON CONFLICT(roll_no) DO UPDATE SET 
                      name=excluded.name, 
                      class_name=excluded.class_name,
                      device_id=excluded.device_id''', 
                   (roll_no, name, class_name, device_id))
    conn.commit()
    conn.close()

def bind_device_to_student(roll_no, device_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET device_id = ? WHERE roll_no = ?", (device_id, roll_no))
    conn.commit()
    conn.close()

def get_student_by_device(device_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT roll_no, name, class_name FROM students WHERE device_id = ?", (device_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def mark_attendance(roll_no, scan_method="DIRECT", session_id="DEFAULT"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%I:%M:%S %p")

    # Check if they are already present for THIS specific session
    cursor.execute("SELECT id FROM attendance_logs WHERE roll_no = ? AND session_id = ? AND date = ?", 
                   (roll_no, session_id, today))
    record = cursor.fetchone()

    is_new = False
    if record:
        # Update their last seen time for this specific session
        cursor.execute("UPDATE attendance_logs SET last_seen = ? WHERE id = ?", (time_now, record[0]))
    else:
        # Create a brand new entry for this session
        cursor.execute("INSERT INTO attendance_logs (roll_no, date, in_time, last_seen, scan_method, session_id) VALUES (?, ?, ?, ?, ?, ?)",
                       (roll_no, today, time_now, time_now, scan_method, session_id))
        is_new = True

    conn.commit()
    conn.close()
    return is_new

# ---------------------------------------------------------
# FIX 2: CONSOLIDATED CSV EXPORT
# I removed the duplicate function and merged the logic so 
# it cleanly handles both single-session and full-day exports.
# ---------------------------------------------------------
def export_logs_to_csv(filepath="attendance_export.csv", session_id=None):
    """
    Exports attendance logs. 
    If session_id is provided, exports ONLY that session.
    Otherwise, exports the full roster for today.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if session_id:
        query = '''
            SELECT s.roll_no, s.name, s.class_name, a.in_time, a.last_seen, a.scan_method, a.session_id 
            FROM students s
            INNER JOIN attendance_logs a ON s.roll_no = a.roll_no AND a.date = ?
            WHERE a.session_id = ?
            ORDER BY s.roll_no ASC
        '''
        cursor.execute(query, (today, session_id))
    else:
        query = '''
            SELECT s.roll_no, s.name, s.class_name, a.in_time, a.last_seen, a.scan_method, a.session_id 
            FROM students s
            LEFT JOIN attendance_logs a ON s.roll_no = a.roll_no AND a.date = ?
            ORDER BY a.session_id DESC, s.roll_no ASC
        '''
        cursor.execute(query, (today,))
        
    rows = cursor.fetchall()
    conn.close()

    # Using utf-8-sig so Excel recognizes the emojis and encoding on Windows
    with open(filepath, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        
        # Headers
        writer.writerow(["Roll Number", "Name", "Class", "Date", "Session ID", "First Seen", "Last Seen", "Method", "Status"]) 
        
        for row in rows:
            roll, name, class_name, in_time, last_seen, method, fetched_session_id = row
            
            # Clean up None values for the CSV
            name = name if name else "Unknown"
            class_name = class_name if class_name else "Unknown"
            display_session = fetched_session_id if fetched_session_id else "N/A"
            
            if in_time: 
                status = "PRESENT ✅"
                time_in = in_time
                time_out = last_seen if last_seen else in_time 
                display_method = method
            else:
                status = "ABSENT ❌"
                time_in = "-"
                time_out = "-"
                display_method = "-"
                display_session = "-"

            writer.writerow([roll, name, class_name, today, display_session, time_in, time_out, display_method, status])
            
    print(f"✅ Exported successfully to {filepath}")

def delete_student(roll_no):
    """Removes a student and all their attendance history from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Delete from the main roster
    cursor.execute("DELETE FROM students WHERE roll_no = ?", (roll_no,))
    # Delete their scan history
    cursor.execute("DELETE FROM attendance_logs WHERE roll_no = ?", (roll_no,))
    conn.commit()
    conn.close()

# Automatically initialize database when script is imported or run
init_db()