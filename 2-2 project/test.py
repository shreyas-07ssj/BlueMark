import asyncio
from bleak import BleakScanner

# Your Android App's UUID (Make sure this matches exactly!)
TARGET_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"

async def run_debug_scan():
    print("--- 🕵️ RAW BLUETOOTH DEBUGGER (FIXED) ---")
    print("Scanning for everything (5 seconds)...")
    
    # 1. Scan
    devices = await BleakScanner.discover(timeout=5.0, return_adv=True)

    print(f"\nFound {len(devices)} total devices.")
    print("-" * 50)

    found_your_app = False

    # 2. Loop through results
    for d, adv in devices.values():
        name = d.name or "Unknown"
        
        # --- THE FIX IS HERE ---
        # We get RSSI from 'adv', not 'd'
        rssi = adv.rssi 
        uuids = [str(u).lower() for u in adv.service_uuids]
        print(uuids)
        
        # Filter for strong signals only (closer than 5 meters)
        # to avoid printing your neighbor's TV
        if rssi > -80:
            print(f"📡 Device: {name}")
            print(f"   MAC Address: {d.address}")
            print(f"   Signal: {rssi} dBm")
            print(f"   Service UUIDs: {uuids}")
            
            # Check for Hidden ID in Service Data
            if adv.service_data:
                print(f"   Service Data (Raw): {adv.service_data}")
                
                # Try to find your specific data
                if TARGET_UUID.lower() in adv.service_data:
                    raw_bytes = adv.service_data[TARGET_UUID.lower()]
                    try:
                        decoded_id = raw_bytes.decode('utf-8')
                        print(f"   ✅ DECODED ID FOUND: {decoded_id}")
                    except:
                        print(f"   ⚠️ Data found but couldn't decode: {raw_bytes}")

            print("-" * 30)

            # Check for Match
            if TARGET_UUID.lower() in uuids:
                found_your_app = True
                print("   🎉 SUCCESS: YOUR APP IS VISIBLE!")

    if not found_your_app:
        print("\n❌ YOUR APP WAS NOT FOUND.")
        print("Tip: Check if 'Location' is turned ON in your phone settings.")
        print("Tip: Check if 'Broadcast' button is GREEN in the App.")

if __name__ == "__main__":
    asyncio.run(run_debug_scan())