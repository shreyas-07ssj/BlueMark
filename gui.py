import db as  db
import customtkinter as ctk
import threading
class RegistrationWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Register New Student")
        self.geometry("450x400")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.title_label = ctk.CTkLabel(self, text="Student Registration", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        self.roll_no_entry = ctk.CTkEntry(self, placeholder_text="Roll Number (e.g., 24X1A0501)", width=300)
        self.roll_no_entry.pack(pady=10)

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Full Name", width=300)
        self.name_entry.pack(pady=10)

        # --- UPDATED: Dropdown Menu for Device IDs ---
        self.id_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.id_frame.pack(pady=10)
        
        self.device_id_var = ctk.StringVar(value="Scan to find devices...")
        self.device_id_dropdown = ctk.CTkOptionMenu(
            self.id_frame, 
            variable=self.device_id_var, 
            values=["Scan to find devices..."], 
            width=200
        )
        self.device_id_dropdown.grid(row=0, column=0, padx=(0, 10))

        self.scan_id_btn = ctk.CTkButton(self.id_frame, text="Scan Room", width=90, command=self.scan_for_devices)
        self.scan_id_btn.grid(row=0, column=1)
        # ---------------------------------------------

        self.save_btn = ctk.CTkButton(self, text="Save to Database", command=self.save_student)
        self.save_btn.pack(pady=20)

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack()

    def scan_for_devices(self):
        """Starts a temporary background scan to find all nearby student phones."""
        self.status_label.configure(text="Scanning for 4 seconds...", text_color="#f39c12")
        self.scan_id_btn.configure(state="disabled")
        self.device_id_dropdown.configure(state="disabled")
        self.update()
        
        threading.Thread(target=self._perform_multi_scan, daemon=True).start()

    def _perform_multi_scan(self):
        import asyncio
        from bleak import BleakScanner

        TARGET_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b".lower()

        async def find_all_devices():
            found_ids = set() # Use a set to prevent duplicate IDs in the dropdown
            devices = await BleakScanner.discover(timeout=4.0, return_adv=True)
            
            for address, (device, adv_data) in devices.items():
                if TARGET_UUID in adv_data.service_data:
                    try:
                        student_id = adv_data.service_data[TARGET_UUID].decode('utf-8')
                        found_ids.add(student_id)
                    except Exception:
                        pass
            return list(found_ids)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        found_ids = loop.run_until_complete(find_all_devices())
        loop.close()

        # Update the GUI based on results
        if found_ids:
            self.after(0, lambda: self._on_scan_success(found_ids))
        else:
            self.after(0, lambda: self._on_scan_fail())

    def _on_scan_success(self, found_ids):
        # Populate the dropdown with the list of found IDs
        self.device_id_dropdown.configure(values=found_ids, state="normal")
        self.device_id_var.set(found_ids[0]) # Auto-select the first one
        self.status_label.configure(text=f"Found {len(found_ids)} device(s). Select one below.", text_color="#2ecc71")
        self.scan_id_btn.configure(state="normal")

    def _on_scan_fail(self):
        self.device_id_dropdown.configure(values=["No devices found"], state="disabled")
        self.device_id_var.set("No devices found")
        self.status_label.configure(text="No devices found. Ensure app is broadcasting.", text_color="#e74c3c")
        self.scan_id_btn.configure(state="normal")

    def save_student(self):
        roll_no = self.roll_no_entry.get().strip()
        name = self.name_entry.get().strip()
        device_id = self.device_id_var.get().strip()

        # Validation to ensure a real ID is selected
        invalid_selections = ["Scan to find devices...", "No devices found", ""]
        if not roll_no or not name or device_id in invalid_selections:
            self.status_label.configure(text="Error: Fill all fields and select a valid Device ID!", text_color="#e74c3c")
            return

        try:
            db.register_student(device_id, roll_no, name)
            self.status_label.configure(text=f"Success: {name} registered to ID {device_id}!", text_color="#2ecc71")
            
            # Reset the form
            self.roll_no_entry.delete(0, 'end')
            self.name_entry.delete(0, 'end')
            self.device_id_dropdown.configure(values=["Scan to find devices..."])
            self.device_id_var.set("Scan to find devices...")
            
            self.after(1500, self.destroy)
        except Exception as e:
            self.status_label.configure(text="Database Error!", text_color="#e74c3c")
            print(f"Registration error: {e}")