# 🔧 Windows Driver Checker & Auto-Updater

Aplikasi GUI Python untuk mengecek, mendownload, dan menginstall driver Windows secara otomatis dengan antarmuka yang modern dan user-friendly.

![Version](https://img.shields.io/badge/version-1.0-blue)
![Python](https://img.shields.io/badge/python-3.7+-green)
![Platform](https://img.shields.io/badge/platform-Windows-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Fitur Utama

- **🔍 Scan Otomatis**: Deteksi semua driver yang terinstall di sistem Windows
- **⚡ Update Checker**: Cek driver mana yang perlu diupdate menggunakan Windows Update API
- **⬇️ Auto Download**: Download driver terbaru secara otomatis
- **📦 Auto Install**: Install driver dengan satu klik
- **🎨 Modern GUI**: Interface yang bersih dan mudah digunakan
- **📊 Detailed Logging**: Log aktivitas lengkap untuk tracking
- **📄 Export Report**: Export laporan driver ke file teks
- **🔒 Admin Check**: Deteksi otomatis privileges administrator
- **✅ Kredibel**: Menggunakan Windows Update API resmi dari Microsoft

## 📋 Requirements

### Sistem Requirements

- **OS**: Windows 7/8/10/11 (64-bit atau 32-bit)
- **Python**: 3.7 atau lebih baru
- **Privileges**: Administrator (untuk install driver)
- **RAM**: Minimal 2GB
- **Storage**: Minimal 500MB free space untuk temporary files

### Python Dependencies

Aplikasi ini menggunakan library built-in Python, tidak ada dependencies eksternal yang wajib:

- `tkinter` (GUI) - Built-in
- `subprocess` - Built-in
- `ctypes` - Built-in
- `threading` - Built-in
- `json` - Built-in
- `logging` - Built-in

## 🚀 Instalasi

### 1. Clone atau Download Repository

```bash
git clone <repository-url>
cd pemrosesan
```

### 2. Install Python (jika belum)

Download Python dari [python.org](https://www.python.org/downloads/)

**Penting**: Centang "Add Python to PATH" saat instalasi!

### 3. Install Dependencies (Optional)

```bash
pip install -r requirements.txt
```

## 💻 Cara Menggunakan

### Method 1: Run as Administrator (Recommended)

1. **Buka Command Prompt sebagai Administrator**
   - Klik kanan pada Command Prompt
   - Pilih "Run as Administrator"

2. **Navigate ke folder aplikasi**
   ```cmd
   cd C:\path\to\pemrosesan
   ```

3. **Jalankan aplikasi**
   ```cmd
   python windows_driver_checker.py
   ```

### Method 2: Run dari File Explorer

1. **Klik kanan pada `windows_driver_checker.py`**
2. **Pilih "Open with" > "Python"**
3. Jika diminta, allow admin privileges

### Method 3: Buat Shortcut

1. Buat file `.bat` baru dengan nama `Run_Driver_Checker.bat`:
   ```batch
   @echo off
   cd /d "%~dp0"
   python windows_driver_checker.py
   pause
   ```

2. Klik kanan pada file `.bat`
3. Pilih "Run as Administrator"

## 📖 Panduan Penggunaan

### 1. Scan Driver

![Scan](https://via.placeholder.com/600x100/3498db/ffffff?text=Klik+Scan+Driver)

- Klik tombol **"🔍 Scan Driver"**
- Tunggu proses scanning selesai (biasanya 30-60 detik)
- Semua driver akan ditampilkan dalam tabel

### 2. Lihat Status Driver

Driver akan ditampilkan dengan warna berbeda:

- 🟢 **Hijau**: Driver up-to-date
- 🟡 **Kuning**: Driver hilang atau perlu perhatian
- 🔴 **Merah**: Driver perlu di-update

### 3. Update Driver

**Update Semua:**
- Klik tombol **"⬇️ Update Semua Driver"**
- Konfirmasi update
- Tunggu proses download & install selesai

**Update Individual:**
- Klik driver yang ingin di-update pada tabel
- Lihat detail di panel log
- Update akan dilakukan otomatis saat klik "Update Semua"

### 4. Export Report

- Klik tombol **"📄 Export Report"**
- File report akan disimpan dengan format: `driver_report_YYYYMMDD_HHMMSS.txt`
- File berisi detail semua driver yang terdeteksi

### 5. Refresh

- Klik tombol **"🔄 Refresh"** untuk scan ulang
- Berguna setelah install driver baru

## 🔧 Fitur Lanjutan

### Windows Update API Integration

Aplikasi ini menggunakan Windows Update COM API untuk:

- Mendapatkan list update driver yang tersedia
- Download driver dari Windows Update secara otomatis
- Install driver dengan aman dan terverifikasi

### Logging System

Semua aktivitas dicatat dalam file `driver_checker.log`:

```
2024-11-03 10:30:15 - INFO - Scanning drivers...
2024-11-03 10:30:45 - INFO - Found 125 drivers
2024-11-03 10:31:00 - WARNING - 5 drivers need update
2024-11-03 10:32:00 - INFO - Driver updated successfully
```

### Driver Detection Methods

Aplikasi menggunakan multiple methods untuk akurasi maksimal:

1. **DISM (Deployment Image Servicing and Management)**
   - Mendapatkan list driver yang terinstall
   - Informasi driver package lengkap

2. **WMI (Windows Management Instrumentation)**
   - Detail hardware device
   - Driver version dan manufacturer

3. **PowerShell**
   - Query Windows Update
   - Driver signature verification

## ⚠️ Troubleshooting

### "Aplikasi harus dijalankan sebagai Administrator"

**Solusi:**
1. Tutup aplikasi
2. Klik kanan pada file/shortcut
3. Pilih "Run as Administrator"

### "Python not found" atau "python is not recognized"

**Solusi:**
1. Install Python dari [python.org](https://www.python.org/downloads/)
2. Centang "Add Python to PATH" saat instalasi
3. Restart Command Prompt

### "No module named 'tkinter'"

**Solusi:**
1. Reinstall Python dengan komponen tcl/tk
2. Atau install tkinter secara manual:
   ```cmd
   python -m pip install tk
   ```

### Driver tidak terdeteksi

**Solusi:**
1. Pastikan aplikasi berjalan sebagai Administrator
2. Update Windows terlebih dahulu
3. Cek koneksi internet (untuk Windows Update)

### Download/Install gagal

**Possible causes:**
- Koneksi internet bermasalah
- Windows Update service tidak running
- Insufficient disk space
- Driver tidak tersedia di Windows Update

**Solusi:**
1. Cek koneksi internet
2. Jalankan Windows Update manual
3. Free up disk space
4. Check Windows Update service:
   ```cmd
   net start wuauserv
   ```

## 🔒 Keamanan

### Verifikasi Driver

Aplikasi hanya menggunakan driver dari sources terpercaya:

✅ Windows Update (Microsoft)
✅ WHQL Signed Drivers
✅ Verified Manufacturers

❌ TIDAK menggunakan third-party driver sites
❌ TIDAK menggunakan unsigned drivers

### Admin Privileges

Admin privileges diperlukan untuk:
- Install driver ke sistem
- Modify system files
- Access hardware information

**Catatan**: Aplikasi TIDAK melakukan:
- Modify registry tanpa izin
- Delete files tanpa konfirmasi
- Send data ke server external

## 📝 Technical Details

### Architecture

```
windows_driver_checker.py (Main GUI)
    ├── GUI Layer (tkinter)
    ├── Driver Scanner
    │   ├── DISM Integration
    │   ├── WMI Query
    │   └── PowerShell Commands
    ├── Update Checker
    │   └── Windows Update API
    └── Logger

windows_update_api.py (API Module)
    ├── WindowsUpdateAPI
    │   ├── search_driver_updates()
    │   └── download_and_install_update()
    ├── DriverDatabase
    │   └── get_latest_driver_version()
    └── DriverBackup
        ├── backup_driver()
        └── restore_driver()
```

### Windows APIs Used

1. **Microsoft.Update.Session** - Windows Update COM Object
2. **DISM API** - Driver enumeration
3. **WMI Win32_PnPSignedDriver** - Device driver information
4. **PnPUtil** - Driver installation utility

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test on Windows system
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

Created with ❤️ for making Windows driver management easier!

## 📞 Support

Jika mengalami masalah:

1. Cek bagian Troubleshooting di atas
2. Lihat log file: `driver_checker.log`
3. Submit issue di GitHub repository

## 🔄 Updates & Changelog

### Version 1.0 (Current)
- Initial release
- Full GUI implementation
- Windows Update API integration
- Auto download & install
- Export report feature
- Comprehensive logging

### Future Plans
- Scheduled automatic updates
- Driver rollback feature
- System restore point creation
- Multiple language support
- Dark mode theme

## ⚡ Performance Tips

1. **First scan may take longer** (1-2 minutes) - subsequent scans are faster
2. **Close unnecessary programs** before updating drivers
3. **Ensure stable internet connection** for downloads
4. **Create system restore point** before major updates
5. **Restart Windows** after driver updates for best results

## 📚 Additional Resources

- [Windows Driver Model](https://docs.microsoft.com/windows-hardware/drivers/)
- [Windows Update API](https://docs.microsoft.com/windows/win32/wua_sdk/)
- [Python Windows Development](https://docs.python.org/3/using/windows.html)

---

**⚠️ DISCLAIMER**: Selalu backup data penting sebelum update driver. Penggunaan aplikasi ini sepenuhnya tanggung jawab pengguna.
