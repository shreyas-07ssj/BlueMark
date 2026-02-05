import asyncio
from bleak import BleakScanner
import db as  db_manager

# YOUR UUID
TARGET_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"

async def register():
    print("--- 📝 REGISTRATION TOOL (FIXED) ---")
    print("Scanning... (Wait 5s)")
    
    # Scan for devices
    devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
    
    candidates = []
    
    for device, adv in devices.values():
        
        # --- NEW LOGIC: Ignore 'service_uuids' list ---
        # We look directly inside the Service Data Dictionary
        
        found_id = None
        
        if adv.service_data:
            # Loop through keys (e.g., '4faf...': b'b4a1')
            for uuid_key, byte_data in adv.service_data.items():
                
                # Check if this Key matches our Target UUID
                if TARGET_UUID.lower() in str(uuid_key).lower():
                    try:
                        # FOUND IT! Decode the ID.
                        found_id = byte_data.decode("utf-8")
                    except:
                        pass
                    break # Stop searching keys

        # If we found an ID, add to list
        if found_id:
            candidates.append((found_id, adv.rssi, device.address))

    if not candidates:
        print("❌ No App found.")
        print("Debug: Ensure Android Status is GREEN (Broadcasting)")
        return

    # Show results
    print(f"\nFound {len(candidates)} device(s):")
    for i, (fid, rssi, mac) in enumerate(candidates):
        print(f"[{i+1}] Student ID: {fid} | Signal: {rssi}")
        
    try:
        sel = int(input("\nSelect #: ")) - 1
        target_id = candidates[sel][0]
        roll = input("Roll No: ").upper().strip()
        name = input("Name: ").strip()
        
        db_manager.init_db()
        db_manager.register_student(target_id, roll, name)
        
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(register())