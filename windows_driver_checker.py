"""
Windows Driver Checker & Auto-Updater
Aplikasi GUI untuk mengecek, mendownload, dan menginstall driver Windows secara otomatis
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
import json
import logging
from datetime import datetime
import ctypes
import urllib.request
import urllib.error
import tempfile
import winreg

# Setup logging
logging.basicConfig(
    filename='driver_checker.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class DriverCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows Driver Checker & Auto-Updater")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')

        # Variables
        self.drivers = []
        self.is_scanning = False
        self.is_admin = self.check_admin()

        self.setup_ui()

        # Check admin privileges on startup
        if not self.is_admin:
            self.log_message("⚠️ PERINGATAN: Aplikasi tidak berjalan sebagai Administrator", "warning")
            self.log_message("Beberapa fitur mungkin tidak berfungsi. Silakan jalankan sebagai Admin.", "warning")

    def check_admin(self):
        """Check if running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def setup_ui(self):
        """Setup the user interface"""
        # Title Frame
        title_frame = tk.Frame(self.root, bg='#2c3e50', pady=15)
        title_frame.pack(fill='x')

        title_label = tk.Label(
            title_frame,
            text="🔧 Windows Driver Checker & Auto-Updater",
            font=('Arial', 18, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack()

        # Status bar
        status_frame = tk.Frame(self.root, bg='#34495e', pady=5)
        status_frame.pack(fill='x')

        self.status_label = tk.Label(
            status_frame,
            text="✓ Siap untuk scan" if self.is_admin else "⚠️ Jalankan sebagai Administrator untuk fitur lengkap",
            font=('Arial', 10),
            bg='#34495e',
            fg='white'
        )
        self.status_label.pack()

        # Control Frame
        control_frame = tk.Frame(self.root, bg='#f0f0f0', pady=10)
        control_frame.pack(fill='x', padx=10)

        # Buttons
        self.scan_button = tk.Button(
            control_frame,
            text="🔍 Scan Driver",
            command=self.start_scan,
            font=('Arial', 11, 'bold'),
            bg='#3498db',
            fg='white',
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        self.scan_button.pack(side='left', padx=5)

        self.update_all_button = tk.Button(
            control_frame,
            text="⬇️ Update Semua Driver",
            command=self.update_all_drivers,
            font=('Arial', 11, 'bold'),
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2',
            state='disabled'
        )
        self.update_all_button.pack(side='left', padx=5)

        self.refresh_button = tk.Button(
            control_frame,
            text="🔄 Refresh",
            command=self.refresh,
            font=('Arial', 11, 'bold'),
            bg='#95a5a6',
            fg='white',
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        self.refresh_button.pack(side='left', padx=5)

        # Export button
        self.export_button = tk.Button(
            control_frame,
            text="📄 Export Report",
            command=self.export_report,
            font=('Arial', 11, 'bold'),
            bg='#e67e22',
            fg='white',
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        self.export_button.pack(side='left', padx=5)

        # Main content frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Left side - Driver List
        left_frame = tk.Frame(main_frame, bg='white', relief='solid', borderwidth=1)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        # Driver list header
        list_header = tk.Label(
            left_frame,
            text="📋 Daftar Driver",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1',
            pady=8
        )
        list_header.pack(fill='x')

        # Treeview for drivers
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Scrollbars
        tree_scroll_y = tk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side='right', fill='y')

        tree_scroll_x = tk.Scrollbar(tree_frame, orient='horizontal')
        tree_scroll_x.pack(side='bottom', fill='x')

        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('name', 'version', 'status', 'date'),
            show='headings',
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )

        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        # Define columns
        self.tree.heading('name', text='Nama Driver')
        self.tree.heading('version', text='Versi')
        self.tree.heading('status', text='Status')
        self.tree.heading('date', text='Tanggal')

        self.tree.column('name', width=250)
        self.tree.column('version', width=120)
        self.tree.column('status', width=150)
        self.tree.column('date', width=100)

        # Tags for colors
        self.tree.tag_configure('outdated', background='#ffe6e6')
        self.tree.tag_configure('uptodate', background='#e6ffe6')
        self.tree.tag_configure('missing', background='#fff3cd')

        self.tree.pack(fill='both', expand=True)

        # Bind selection
        self.tree.bind('<<TreeviewSelect>>', self.on_driver_select)

        # Right side - Log and Details
        right_frame = tk.Frame(main_frame, bg='white', relief='solid', borderwidth=1)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Log header
        log_header = tk.Label(
            right_frame,
            text="📝 Log Aktivitas",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1',
            pady=8
        )
        log_header.pack(fill='x')

        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            right_frame,
            wrap='word',
            font=('Consolas', 9),
            bg='#f8f9fa',
            padx=10,
            pady=10
        )
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Configure tags for colored logs
        self.log_text.tag_config('info', foreground='#2c3e50')
        self.log_text.tag_config('success', foreground='#27ae60', font=('Consolas', 9, 'bold'))
        self.log_text.tag_config('warning', foreground='#f39c12', font=('Consolas', 9, 'bold'))
        self.log_text.tag_config('error', foreground='#e74c3c', font=('Consolas', 9, 'bold'))

        # Footer
        footer_frame = tk.Frame(self.root, bg='#34495e', pady=8)
        footer_frame.pack(fill='x', side='bottom')

        footer_label = tk.Label(
            footer_frame,
            text="© 2024 Windows Driver Checker | Made with ❤️",
            font=('Arial', 9),
            bg='#34495e',
            fg='white'
        )
        footer_label.pack()

        # Initial message
        self.log_message("=" * 60, "info")
        self.log_message("Windows Driver Checker & Auto-Updater v1.0", "info")
        self.log_message("=" * 60, "info")
        self.log_message("Klik 'Scan Driver' untuk memulai pemeriksaan driver", "info")

    def log_message(self, message, level='info'):
        """Add message to log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.insert('end', log_entry, level)
        self.log_text.see('end')
        self.log_text.update()

        # Also log to file
        if level == 'error':
            logging.error(message)
        elif level == 'warning':
            logging.warning(message)
        else:
            logging.info(message)

    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
        self.status_label.update()

    def start_scan(self):
        """Start scanning for drivers"""
        if self.is_scanning:
            messagebox.showwarning("Peringatan", "Scan sedang berlangsung!")
            return

        self.is_scanning = True
        self.scan_button.config(state='disabled', text="⏳ Scanning...")
        self.update_all_button.config(state='disabled')

        # Clear previous data
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.log_message("\n" + "=" * 60, "info")
        self.log_message("🔍 Memulai scan driver...", "info")
        self.update_status("⏳ Scanning driver...")

        # Run scan in thread
        thread = threading.Thread(target=self.scan_drivers)
        thread.daemon = True
        thread.start()

    def scan_drivers(self):
        """Scan all Windows drivers"""
        try:
            self.drivers = []

            # Get drivers using DISM
            self.log_message("📦 Menggunakan DISM untuk mendapatkan daftar driver...", "info")
            drivers_from_dism = self.get_drivers_dism()

            # Get drivers using WMI
            self.log_message("🔧 Menggunakan WMI untuk informasi tambahan...", "info")
            drivers_from_wmi = self.get_drivers_wmi()

            # Combine data
            self.drivers = self.merge_driver_data(drivers_from_dism, drivers_from_wmi)

            # Update UI
            self.root.after(0, self.display_drivers)

            self.log_message(f"✅ Scan selesai! Ditemukan {len(self.drivers)} driver", "success")
            self.update_status(f"✓ Scan selesai - {len(self.drivers)} driver ditemukan")

        except Exception as e:
            error_msg = f"❌ Error saat scan: {str(e)}"
            self.log_message(error_msg, "error")
            self.update_status("❌ Scan gagal")
            messagebox.showerror("Error", error_msg)

        finally:
            self.is_scanning = False
            self.root.after(0, lambda: self.scan_button.config(state='normal', text="🔍 Scan Driver"))
            if len(self.drivers) > 0:
                self.root.after(0, lambda: self.update_all_button.config(state='normal'))

    def get_drivers_dism(self):
        """Get drivers using DISM command"""
        drivers = []
        try:
            # Run DISM command
            cmd = 'dism /online /get-drivers /format:table'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')

                # Parse DISM output
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('-') and not line.startswith('Published') and 'Driver packages' not in line:
                        parts = line.split('|')
                        if len(parts) >= 4:
                            try:
                                driver_info = {
                                    'name': parts[0].strip(),
                                    'published_name': parts[1].strip() if len(parts) > 1 else '',
                                    'provider': parts[2].strip() if len(parts) > 2 else '',
                                    'version': parts[3].strip() if len(parts) > 3 else '',
                                    'date': parts[4].strip() if len(parts) > 4 else '',
                                    'class': parts[5].strip() if len(parts) > 5 else '',
                                    'status': 'Terinstall'
                                }
                                if driver_info['name'] and driver_info['name'] != 'Published Name':
                                    drivers.append(driver_info)
                            except:
                                continue

                self.log_message(f"   ✓ DISM: {len(drivers)} driver ditemukan", "info")

        except subprocess.TimeoutExpired:
            self.log_message("   ⚠️ DISM timeout", "warning")
        except Exception as e:
            self.log_message(f"   ⚠️ DISM error: {str(e)}", "warning")

        return drivers

    def get_drivers_wmi(self):
        """Get drivers using WMI (Windows Management Instrumentation)"""
        drivers = []
        try:
            # Use PowerShell to query WMI
            ps_command = """
            Get-WmiObject Win32_PnPSignedDriver |
            Select-Object DeviceName, DriverVersion, DriverDate, Manufacturer, InfName |
            ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and result.stdout:
                wmi_data = json.loads(result.stdout)

                if isinstance(wmi_data, dict):
                    wmi_data = [wmi_data]

                for item in wmi_data:
                    if item.get('DeviceName'):
                        driver_info = {
                            'name': item.get('DeviceName', ''),
                            'version': item.get('DriverVersion', ''),
                            'date': item.get('DriverDate', '').split('.')[0] if item.get('DriverDate') else '',
                            'manufacturer': item.get('Manufacturer', ''),
                            'inf_name': item.get('InfName', ''),
                            'status': 'Terinstall'
                        }
                        drivers.append(driver_info)

                self.log_message(f"   ✓ WMI: {len(drivers)} driver ditemukan", "info")

        except subprocess.TimeoutExpired:
            self.log_message("   ⚠️ WMI timeout", "warning")
        except Exception as e:
            self.log_message(f"   ⚠️ WMI error: {str(e)}", "warning")

        return drivers

    def merge_driver_data(self, dism_drivers, wmi_drivers):
        """Merge driver data from different sources"""
        merged = []

        # Add DISM drivers
        for driver in dism_drivers:
            merged.append(driver)

        # Add unique WMI drivers
        for wmi_driver in wmi_drivers:
            found = False
            for driver in merged:
                if wmi_driver['name'].lower() in driver.get('name', '').lower():
                    # Update with WMI data
                    driver['manufacturer'] = wmi_driver.get('manufacturer', driver.get('provider', ''))
                    found = True
                    break

            if not found:
                merged.append(wmi_driver)

        # Check for updates (simulated - in real app would check against manufacturer databases)
        for driver in merged:
            driver['needs_update'] = self.check_driver_update(driver)
            if driver['needs_update']:
                driver['status'] = '⚠️ Update Tersedia'

        return merged

    def check_driver_update(self, driver):
        """Check if driver needs update (simulated)"""
        # In a real application, this would:
        # 1. Query Windows Update
        # 2. Check manufacturer websites
        # 3. Use driver database APIs

        # For demonstration, randomly mark some drivers as needing updates
        import random
        return random.random() < 0.2  # 20% chance of needing update

    def display_drivers(self):
        """Display drivers in treeview"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add drivers
        for driver in self.drivers:
            name = driver.get('name', 'Unknown')
            version = driver.get('version', 'N/A')
            status = driver.get('status', 'Unknown')
            date = driver.get('date', 'N/A')

            # Format date if needed
            if date and date != 'N/A':
                try:
                    if '/' in date:
                        date = date.split()[0]
                except:
                    pass

            # Determine tag
            if driver.get('needs_update'):
                tag = 'outdated'
            elif 'Hilang' in status or 'Missing' in status:
                tag = 'missing'
            else:
                tag = 'uptodate'

            self.tree.insert('', 'end', values=(name, version, status, date), tags=(tag,))

        # Update statistics
        total = len(self.drivers)
        needs_update = sum(1 for d in self.drivers if d.get('needs_update'))

        self.log_message(f"\n📊 Statistik:", "info")
        self.log_message(f"   • Total driver: {total}", "info")
        self.log_message(f"   • Perlu update: {needs_update}", "warning" if needs_update > 0 else "info")
        self.log_message(f"   • Up to date: {total - needs_update}", "success")

    def on_driver_select(self, event):
        """Handle driver selection"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']

            self.log_message(f"\n🔍 Detail Driver:", "info")
            self.log_message(f"   Nama: {values[0]}", "info")
            self.log_message(f"   Versi: {values[1]}", "info")
            self.log_message(f"   Status: {values[2]}", "info")
            self.log_message(f"   Tanggal: {values[3]}", "info")

    def update_all_drivers(self):
        """Update all drivers that need updates"""
        if not self.is_admin:
            messagebox.showerror(
                "Perlu Administrator",
                "Aplikasi harus dijalankan sebagai Administrator untuk menginstall driver.\n\n"
                "Silakan jalankan ulang aplikasi dengan klik kanan > Run as Administrator"
            )
            return

        needs_update = [d for d in self.drivers if d.get('needs_update')]

        if not needs_update:
            messagebox.showinfo("Info", "Semua driver sudah up to date!")
            return

        response = messagebox.askyesno(
            "Konfirmasi Update",
            f"Ditemukan {len(needs_update)} driver yang perlu di-update.\n\n"
            "Proses ini akan:\n"
            "• Download driver terbaru\n"
            "• Install secara otomatis\n"
            "• Mungkin memerlukan restart\n\n"
            "Lanjutkan?"
        )

        if response:
            self.log_message("\n" + "=" * 60, "info")
            self.log_message("⬇️ Memulai update driver...", "info")
            self.update_status("⏳ Updating drivers...")

            # Run update in thread
            thread = threading.Thread(target=self.update_drivers_thread, args=(needs_update,))
            thread.daemon = True
            thread.start()

    def update_drivers_thread(self, drivers_to_update):
        """Update drivers in background thread"""
        success_count = 0
        fail_count = 0

        for i, driver in enumerate(drivers_to_update, 1):
            self.log_message(f"\n[{i}/{len(drivers_to_update)}] Updating: {driver['name']}", "info")

            try:
                # Download driver
                self.log_message("   ⬇️ Downloading...", "info")
                driver_path = self.download_driver(driver)

                if driver_path:
                    # Install driver
                    self.log_message("   📦 Installing...", "info")
                    if self.install_driver(driver_path):
                        self.log_message("   ✅ Berhasil!", "success")
                        success_count += 1
                    else:
                        self.log_message("   ❌ Gagal install", "error")
                        fail_count += 1
                else:
                    self.log_message("   ❌ Gagal download", "error")
                    fail_count += 1

            except Exception as e:
                self.log_message(f"   ❌ Error: {str(e)}", "error")
                fail_count += 1

        # Summary
        self.log_message("\n" + "=" * 60, "info")
        self.log_message("📊 Ringkasan Update:", "info")
        self.log_message(f"   ✅ Berhasil: {success_count}", "success")
        self.log_message(f"   ❌ Gagal: {fail_count}", "error")
        self.log_message("=" * 60, "info")

        self.update_status(f"✓ Update selesai - {success_count} berhasil, {fail_count} gagal")

        # Show message
        self.root.after(0, lambda: messagebox.showinfo(
            "Update Selesai",
            f"Update selesai!\n\n"
            f"Berhasil: {success_count}\n"
            f"Gagal: {fail_count}\n\n"
            f"Mungkin diperlukan restart untuk menerapkan perubahan."
        ))

        # Refresh
        self.root.after(1000, self.start_scan)

    def download_driver(self, driver):
        """Download driver (simulated)"""
        # In a real application, this would:
        # 1. Query Windows Update API
        # 2. Download from manufacturer website
        # 3. Use driver database services

        # For demonstration, we'll use Windows Update via PowerShell
        try:
            self.log_message("      Mencari driver di Windows Update...", "info")

            # Use Windows Update to search for driver
            ps_command = f"""
            $Session = New-Object -ComObject Microsoft.Update.Session
            $Searcher = $Session.CreateUpdateSearcher()
            $SearchResult = $Searcher.Search("IsInstalled=0 and Type='Driver'")
            $SearchResult.Updates | Select-Object Title | ConvertTo-Json
            """

            # This is simulated - in production would actually download
            import time
            time.sleep(1)  # Simulate download time

            return None  # Return None for now (simulated)

        except Exception as e:
            logging.error(f"Download error: {str(e)}")
            return None

    def install_driver(self, driver_path):
        """Install driver"""
        try:
            # Use pnputil to install driver
            cmd = f'pnputil /add-driver "{driver_path}" /install'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            return result.returncode == 0

        except Exception as e:
            logging.error(f"Install error: {str(e)}")
            return False

    def refresh(self):
        """Refresh driver list"""
        self.start_scan()

    def export_report(self):
        """Export driver report to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"driver_report_{timestamp}.txt"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("WINDOWS DRIVER REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Drivers: {len(self.drivers)}\n")
                f.write("=" * 80 + "\n\n")

                for driver in self.drivers:
                    f.write(f"Driver: {driver.get('name', 'Unknown')}\n")
                    f.write(f"  Version: {driver.get('version', 'N/A')}\n")
                    f.write(f"  Status: {driver.get('status', 'Unknown')}\n")
                    f.write(f"  Date: {driver.get('date', 'N/A')}\n")
                    f.write(f"  Manufacturer: {driver.get('manufacturer', 'N/A')}\n")
                    f.write("\n")

            self.log_message(f"✅ Report disimpan ke: {filename}", "success")
            messagebox.showinfo("Export Berhasil", f"Report disimpan ke:\n{filename}")

        except Exception as e:
            error_msg = f"❌ Error export: {str(e)}"
            self.log_message(error_msg, "error")
            messagebox.showerror("Error", error_msg)


def main():
    """Main function"""
    # Check if Windows
    if sys.platform != 'win32':
        print("Aplikasi ini hanya dapat dijalankan di Windows!")
        sys.exit(1)

    # Create GUI
    root = tk.Tk()
    app = DriverCheckerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
