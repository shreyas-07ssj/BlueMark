import asyncio
import time
from datetime import datetime
from bleak import BleakScanner
import db

TARGET_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b".lower()

async def async_scanner(gui_queue, stop_event, session_memory, session_id):
    print(f"BLE Scanner actively listening for {session_id}...")
    
    while not stop_event.is_set():
        devices = await BleakScanner.discover(timeout=2.0, return_adv=True)
        current_time = time.time()
        
        for address, (device, adv_data) in devices.items():
            if TARGET_UUID in adv_data.service_data:
                try:
                    payload = adv_data.service_data[TARGET_UUID].decode('utf-8')
                    
                    # --- The Software Cooldown ---
                    # Prevent database spam by waiting 60 seconds between updates
                    if payload not in session_memory or (current_time - session_memory[payload] > 60):
                        process_student(payload, gui_queue, session_id)
                        session_memory[payload] = current_time
                        
                except Exception as e:
                    print(f"Decode Error: {e}")
                    
        await asyncio.sleep(0.5)

def process_student(payload_string, gui_queue, session_id):
    """Decodes the Mesh payload and routes the IDs."""
    parts = payload_string.split('|vouch:')
    primary_device_id = parts[0]
    
    # 1. Log the student whose phone the laptop actually heard
    _log_individual(primary_device_id, gui_queue, "DIRECT", session_id)

    # 2. Log the student who was relayed (if it's a mesh payload)
    if len(parts) > 1:
        vouched_device_id = parts[1]
        _log_individual(vouched_device_id, gui_queue, "MESH RELAY", session_id)

def _log_individual(device_id, gui_queue, method, session_id):
    """Checks the database and updates the GUI."""
    student_info = db.get_student_by_device(device_id)
    
    if student_info:
        roll_no, name, class_name = student_info
        is_first_scan = db.mark_attendance(roll_no, method, session_id)
        
        if is_first_scan:
            time_now = datetime.now().strftime("%I:%M:%S %p")
            # Send to GUI
            gui_queue.put((roll_no, name, time_now, method))
            print(f"✅ [{method}] Arrived: {name} ({class_name})")
        else:
            # Silent update for the audit trail
            print(f"🔄 [{method}] Updated background clock for: {name}") 
    else:
        # Save to a separate queue or variable if you want to capture unbound IDs for the GUI later
        print(f"⚠️ Unbound device detected: {device_id}")
        gui_queue.put(("UNBOUND", device_id, "N/A", "N/A"))

def run_scanner(gui_queue, stop_event, session_id):
    """Entry point for the background thread."""
    session_memory = {} 
    try:
        asyncio.run(async_scanner(gui_queue, stop_event, session_memory, session_id))
    except Exception as e:
        print(f"Scanner Error: {e}")