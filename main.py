import customtkinter as ctk
from tkinter import ttk
import threading
import queue
from datetime import datetime
import db
import teacher 

# Configure Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StudentManagementWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Student Roster & Device Binding")
        self.geometry("750x550")
        self.attributes("-topmost", True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL: DATA ENTRY ---
        self.entry_frame = ctk.CTkFrame(self)
        self.entry_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.entry_frame, text="Add / Edit Student", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        self.roll_entry = ctk.CTkEntry(self.entry_frame, placeholder_text="Roll Number")
        self.roll_entry.pack(pady=10, padx=20, fill="x")

        self.name_entry = ctk.CTkEntry(self.entry_frame, placeholder_text="Full Name")
        self.name_entry.pack(pady=10, padx=20, fill="x")

        self.class_entry = ctk.CTkEntry(self.entry_frame, placeholder_text="Class")
        self.class_entry.pack(pady=10, padx=20, fill="x")

        self.save_btn = ctk.CTkButton(self.entry_frame, text="Save to Roster", command=self.save_student)
        self.save_btn.pack(pady=20, padx=20, fill="x")

        self.status_label = ctk.CTkLabel(self.entry_frame, text="", text_color="gray")
        self.status_label.pack(pady=5)

        # --- RIGHT PANEL: ROSTER & BINDING ---
        self.roster_frame = ctk.CTkFrame(self)
        self.roster_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.roster_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.roster_frame, text="Current Roster", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=10)

        columns = ("Roll No", "Name", "Class", "Device Status")
        self.tree = ttk.Treeview(self.roster_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.bind_frame = ctk.CTkFrame(self.roster_frame, fg_color="transparent")
        self.bind_frame.grid(row=2, column=0, pady=10)

        self.scan_btn = ctk.CTkButton(self.bind_frame, text="1. Scan Phone", command=self.scan_for_device)
        self.scan_btn.grid(row=0, column=0, padx=5)

        self.device_var = ctk.StringVar(value="No device scanned")
        self.device_menu = ctk.CTkOptionMenu(self.bind_frame, variable=self.device_var, values=["No device scanned"], state="disabled")
        self.device_menu.grid(row=0, column=1, padx=5)

        self.bind_btn = ctk.CTkButton(self.bind_frame, text="2. Bind to Selected Student", command=self.bind_device, fg_color="#27ae60", hover_color="#2ecc71")
        self.bind_btn.grid(row=0, column=2, padx=5)

        self.delete_btn = ctk.CTkButton(self.roster_frame, text="🗑️ Delete Selected Student", command=self.delete_selected, fg_color="#e74c3c", hover_color="#c0392b")
        self.delete_btn.grid(row=3, column=0, pady=10)
        
        self.refresh_roster()

    def save_student(self):
        roll, name, cls = self.roll_entry.get().strip(), self.name_entry.get().strip(), self.class_entry.get().strip()
        if roll and name and cls:
            db.add_or_edit_student(roll, name, cls)
            self.status_label.configure(text=f"Saved: {name}", text_color="#2ecc71")
            self.refresh_roster()

    def refresh_roster(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        import sqlite3
        conn = sqlite3.connect("attendance.db")
        for row in conn.execute("SELECT roll_no, name, class_name, device_id FROM students"):
            status = "✅ Bound" if row[3] else "❌ Unbound"
            self.tree.insert("", "end", values=(row[0], row[1], row[2], status))
        conn.close()

    def scan_for_device(self):
        self.scan_btn.configure(text="Scanning...", state="disabled")
        threading.Thread(target=self._perform_scan, daemon=True).start()

    def _perform_scan(self):
        import asyncio
        from bleak import BleakScanner
        TARGET_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b".lower()
        async def find_device():
            devices = await BleakScanner.discover(timeout=4.0, return_adv=True)
            found = set()
            for address, (device, adv_data) in devices.items():
                if TARGET_UUID in adv_data.service_data:
                    try:
                        payload = adv_data.service_data[TARGET_UUID].decode('utf-8')
                        found.add(payload.split('|vouch:')[0])
                    except: pass
            return list(found)
        loop = asyncio.new_event_loop()
        found_ids = loop.run_until_complete(find_device())
        self.after(0, lambda: self._on_scan_success(found_ids) if found_ids else self._on_scan_fail())

    def _on_scan_success(self, found_ids):
        self.device_menu.configure(values=found_ids, state="normal")
        self.device_var.set(found_ids[0])
        self.scan_btn.configure(text="1. Scan Phone", state="normal")

    def _on_scan_fail(self):
        self.device_menu.configure(values=["No devices found"], state="disabled")
        self.device_var.set("No devices found")
        self.scan_btn.configure(text="1. Scan Phone", state="normal")

    def bind_device(self):
        selected = self.tree.selection()
        if selected and self.device_var.get() not in ["No device scanned", "No devices found"]:
            roll_no = self.tree.item(selected[0])['values'][0]
            db.bind_device_to_student(str(roll_no), self.device_var.get())
            self.refresh_roster()

    def delete_selected(self):
        selected = self.tree.selection()
        if selected:
            db.delete_student(str(self.tree.item(selected[0])['values'][0]))
            self.refresh_roster()

class TeacherGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BlueMesh Attendance Console")
        self.geometry("950x650")

        self.data_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.scan_thread = None
        self.current_session_id = "None"
        self.attendance_count = 0

        self._build_sidebar()
        self._build_main_view()

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="DASHBOARD", font=("Arial", 20, "bold")).grid(row=0, column=0, pady=20)

        # Session Naming
        ctk.CTkLabel(self.sidebar, text="Session Name:", font=("Arial", 12)).grid(row=1, column=0, pady=(10, 0))
        self.session_entry = ctk.CTkEntry(self.sidebar, placeholder_text="e.g. Lab_1", width=160)
        self.session_entry.grid(row=2, column=0, padx=20, pady=5)
        self.session_entry.insert(0, "Class_A")

        self.start_btn = ctk.CTkButton(self.sidebar, text="▶ Start Class", fg_color="#27ae60", command=self.start_scan)
        self.start_btn.grid(row=3, column=0, padx=20, pady=10)

        self.stop_btn = ctk.CTkButton(self.sidebar, text="⏹ End Class", command=self.stop_scan, fg_color="transparent", border_width=2)
        self.stop_btn.grid(row=4, column=0, padx=20, pady=10)

        self.export_btn = ctk.CTkButton(self.sidebar, text="📊 Export CSV", command=self.export_data)
        self.export_btn.grid(row=5, column=0, padx=20, pady=10)

        self.roster_btn = ctk.CTkButton(self.sidebar, text="📝 Manage Roster", command=self.open_roster_manager)
        self.roster_btn.grid(row=6, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Ready", text_color="white")
        self.status_label.grid(row=7, column=0, padx=20, pady=20)

    def _build_main_view(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.header_label = ctk.CTkLabel(self.main_frame, text="Live Attendance Log", font=("Arial", 24, "bold"))
        self.header_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        self.tree = ttk.Treeview(self.main_frame, columns=("Roll Number", "Name", "Time", "Status"), show="headings")
        for col in ("Roll Number", "Name", "Time", "Status"):
            self.tree.heading(col, text=col); self.tree.column(col, anchor="center")
        self.tree.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        # Live Counter
        self.stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.stats_frame.grid(row=2, column=0, pady=10, sticky="ew")
        self.counter_label = ctk.CTkLabel(self.stats_frame, text="Students Present: 0", font=("Arial", 16, "bold"), text_color="#3498db")
        self.counter_label.pack(side="right", padx=30)

    def open_roster_manager(self):
        if not hasattr(self, 'roster_window') or not self.roster_window.winfo_exists():
            self.roster_window = StudentManagementWindow(self)
        self.roster_window.focus()

    def start_scan(self):
        """THIS IS YOUR RESET BUTTON - IT CLEARS EVERYTHING"""
        if self.scan_thread and self.scan_thread.is_alive(): return
        
        # 1. CLEAN THE SLATE (No more names from previous session)
        self.attendance_count = 0
        self.counter_label.configure(text="Students Present: 0")
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        # 2. GENERATE UNIQUE SESSION
        session_name = self.session_entry.get().strip().replace(" ", "_") or "Session"
        self.current_session_id = f"{session_name}_{datetime.now().strftime('%H%M%S')}"
        
        self.status_label.configure(text=f"Active: {session_name}", text_color="#2ecc71")
        self.stop_event.clear()
        
        # 3. START FRESH BACKGROUND THREAD
        self.scan_thread = threading.Thread(target=teacher.run_scanner, 
                                            args=(self.data_queue, self.stop_event, self.current_session_id), 
                                            daemon=True)
        self.scan_thread.start()
        self.check_queue_for_data()

    def stop_scan(self):
        self.status_label.configure(text="Status: Stopped", text_color="#e74c3c")
        self.stop_event.set()

    def check_queue_for_data(self):
        try:
            while True:
                data = self.data_queue.get_nowait()
                if data[0] != "UNBOUND":
                    # Only insert if the student isn't already visible in THIS session
                    existing = [self.tree.item(i)['values'][0] for i in self.tree.get_children()]
                    if str(data[0]) not in existing:
                        self.tree.insert("", "end", values=data)
                        self.attendance_count += 1
                        self.counter_label.configure(text=f"Students Present: {self.attendance_count}")
        except queue.Empty: pass
        if self.scan_thread and self.scan_thread.is_alive():
            self.after(500, self.check_queue_for_data)

    def export_data(self):
        try:
            db.export_logs_to_csv(session_id=self.current_session_id)
            self.status_label.configure(text="Exported Successfully! ✅", text_color="#2ecc71")
        except Exception as e:
            print(f"Export Error: {e}")

if __name__ == "__main__":
    db.init_db()
    app = TeacherGUI(); app.mainloop()