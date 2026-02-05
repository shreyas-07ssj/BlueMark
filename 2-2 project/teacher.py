import asyncio
from bleak import BleakScanner
import db as db_manager
import csv
import sqlite3
from datetime import datetime

TARGET_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
present_students = {} 

# --- 1. CONFIGURATION: Map Branch Names to Codes ---
BRANCH_MAP = {
    "CSE": "05",
    "ECE": "04",
    "EEE": "02",
    "MECH": "03",
    "CIVIL": "01",
    "IT": "12",
    "CSM": "66", # AI & ML often use 66 or similar
    "CSD": "67"  # Data Science
}

print("--- 🏫 BLUE MESH ATTENDANCE ---")
print("Available Branches:", ", ".join(BRANCH_MAP.keys()))

while True:
    user_input = input("Enter Branch (e.g., CSE): ").strip().upper()
    
    if user_input in BRANCH_MAP:
        TARGET_CODE = BRANCH_MAP[user_input]
        TARGET_BRANCH_NAME = user_input
        break
    else:
        print(f"❌ Unknown branch '{user_input}'. Try again.")

print(f"\n🔒 LOCKED: Class '{TARGET_BRANCH_NAME}'")
print(f"🎯 FILTER: Only accepting Roll Numbers with '{TARGET_CODE}'")
print("-" * 40)

def generate_excel_report():
    print("\n\n📊 Generating Excel Report...", end="")
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT roll_no, name FROM registry ORDER BY roll_no ASC")
        all_students = cursor.fetchall()
        conn.close()
        
        filename = f"Attendance_{TARGET_BRANCH_NAME}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
        
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Roll Number", "Name", "Time In", "Last Seen", "Duration (min)", "Status"])
            
            for (roll, name) in all_students:
                # FILTER: Only include students belonging to this branch
                if TARGET_CODE in roll:
                    if roll in present_students:
                        data = present_students[roll]
                        t_in, t_last = data['in'], data['last']
                        
                        fmt = "%H:%M:%S"
                        d1 = datetime.strptime(t_in, fmt)
                        d2 = datetime.strptime(t_last, fmt)
                        dur = int((d2 - d1).total_seconds() / 60)
                        
                        status = "PRESENT"
                    else:
                        t_in, t_last, dur = "--", "--", 0
                        status = "ABSENT"
                    
                    writer.writerow([roll, name, t_in, t_last, dur, status])

        print(f" Done! \n✅ Saved: {filename}")
        print("👋 Class Ended.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

async def main():
    print(f"Scanning for {TARGET_BRANCH_NAME} students...")
    print("Press Ctrl+C to stop.")
    db_manager.init_db()
    
    def callback(device, adv):
        if adv.service_data:
            for uuid_key, byte_data in adv.service_data.items():
                if TARGET_UUID.lower() in str(uuid_key).lower():
                    try:
                        fid = byte_data.decode("utf-8")
                        student = db_manager.get_student_identity(fid)
                        
                        if student:
                            roll, name = student
                            
                            # --- STRICT POSITION CHECK ---
                            # Example: 21ss1a0523
                            # Indices: 0123456789
                            # We want characters at index 6 and 7 ("05")
                            
                            try:
                                # Extract specific branch code from the middle of the string
                                student_branch_code = roll[6:8] 
                                
                                if student_branch_code == TARGET_CODE:
                                    now_time = datetime.now().strftime("%H:%M:%S")
                                    
                                    if roll not in present_students:
                                        print(f"✅ DETECTED: {name} ({roll})")
                                        present_students[roll] = {'name': name, 'in': now_time, 'last': now_time}
                                        db_manager.mark_final_attendance(roll, "PRESENT")
                                    else:
                                        present_students[roll]['last'] = now_time
                            except IndexError:
                                # In case a weird/short roll number is entered
                                pass
                                
                    except:
                        pass
                    break

    scanner = BleakScanner(callback)
    
    try:
        await scanner.start()
        while True: await asyncio.sleep(1)     
    except KeyboardInterrupt:
        print("\n🛑 Stopping Scanner...")
        await scanner.stop() 
    finally:
        generate_excel_report()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass