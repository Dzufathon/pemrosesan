"""
Driver Utilities
Helper functions untuk driver management
"""

import subprocess
import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime


logger = logging.getLogger(__name__)


def is_admin() -> bool:
    """Check if script is running with administrator privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def request_admin_privileges():
    """Request admin privileges if not already running as admin"""
    if not is_admin():
        try:
            import ctypes
            import sys

            # Re-run the script with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
        except Exception as e:
            logger.error(f"Failed to request admin privileges: {e}")
            return False
    return True


def get_system_info() -> Dict:
    """Get Windows system information"""
    try:
        ps_script = """
        $os = Get-WmiObject Win32_OperatingSystem
        $cs = Get-WmiObject Win32_ComputerSystem

        @{
            OSName = $os.Caption
            OSVersion = $os.Version
            OSBuild = $os.BuildNumber
            ComputerName = $cs.Name
            Manufacturer = $cs.Manufacturer
            Model = $cs.Model
            TotalMemoryGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)
        } | ConvertTo-Json
        """

        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}


def check_windows_update_service() -> bool:
    """Check if Windows Update service is running"""
    try:
        result = subprocess.run(
            ['sc', 'query', 'wuauserv'],
            capture_output=True,
            text=True,
            timeout=10
        )

        return 'RUNNING' in result.stdout
    except Exception as e:
        logger.error(f"Error checking Windows Update service: {e}")
        return False


def start_windows_update_service() -> bool:
    """Start Windows Update service if not running"""
    try:
        result = subprocess.run(
            ['net', 'start', 'wuauserv'],
            capture_output=True,
            text=True,
            timeout=30
        )

        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error starting Windows Update service: {e}")
        return False


def get_driver_details_wmi(device_id: str) -> Optional[Dict]:
    """Get detailed driver information for a specific device"""
    try:
        ps_script = f"""
        Get-WmiObject Win32_PnPSignedDriver |
        Where-Object {{$_.DeviceID -eq "{device_id}"}} |
        Select-Object DeviceName, DriverVersion, DriverDate, Manufacturer,
                      InfName, IsSigned, Signer, HardWareID |
        ConvertTo-Json
        """

        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
        return None
    except Exception as e:
        logger.error(f"Error getting driver details: {e}")
        return None


def verify_driver_integrity(driver_path: str) -> Tuple[bool, str]:
    """Verify driver file integrity and signature"""
    try:
        ps_script = f"""
        $signature = Get-AuthenticodeSignature -FilePath "{driver_path}"

        @{{
            Status = $signature.Status.ToString()
            StatusMessage = $signature.StatusMessage
            SignerCertificate = $signature.SignerCertificate.Subject
            TimeStamper = $signature.TimeStamperCertificate.Subject
            IsOSBinary = $signature.IsOSBinary
        }} | ConvertTo-Json
        """

        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout:
            sig_info = json.loads(result.stdout)
            is_valid = sig_info.get('Status') == 'Valid'
            message = sig_info.get('StatusMessage', 'Unknown')
            return is_valid, message

        return False, "Unable to verify signature"
    except Exception as e:
        logger.error(f"Error verifying driver integrity: {e}")
        return False, str(e)


def create_system_restore_point(description: str = "Before Driver Update") -> bool:
    """Create a system restore point before making changes"""
    try:
        ps_script = f"""
        try {{
            Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS"
            Write-Output "Success"
        }} catch {{
            Write-Error $_.Exception.Message
        }}
        """

        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=60
        )

        return "Success" in result.stdout
    except Exception as e:
        logger.error(f"Error creating restore point: {e}")
        return False


def get_problematic_devices() -> List[Dict]:
    """Get list of devices with problems (missing or malfunctioning drivers)"""
    try:
        ps_script = """
        Get-WmiObject Win32_PNPEntity |
        Where-Object {$_.ConfigManagerErrorCode -ne 0} |
        Select-Object Name, DeviceID, ConfigManagerErrorCode, Status |
        ConvertTo-Json
        """

        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0 and result.stdout:
            devices = json.loads(result.stdout)
            if isinstance(devices, dict):
                devices = [devices]
            return devices
        return []
    except Exception as e:
        logger.error(f"Error getting problematic devices: {e}")
        return []


def export_driver(driver_name: str, export_path: str) -> bool:
    """Export an installed driver to a folder"""
    try:
        # Create export directory if it doesn't exist
        os.makedirs(export_path, exist_ok=True)

        ps_script = f"""
        $driver = Get-WindowsDriver -Online |
                  Where-Object {{$_.ProviderName -like "*{driver_name}*"}} |
                  Select-Object -First 1

        if ($driver) {{
            Export-WindowsDriver -Online -Destination "{export_path}" -Driver $driver.Driver
            Write-Output "Success"
        }} else {{
            Write-Error "Driver not found"
        }}
        """

        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=120
        )

        return "Success" in result.stdout
    except Exception as e:
        logger.error(f"Error exporting driver: {e}")
        return False


def uninstall_driver(driver_inf: str) -> bool:
    """Uninstall a driver using pnputil"""
    try:
        cmd = f'pnputil /delete-driver {driver_inf} /uninstall'
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )

        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error uninstalling driver: {e}")
        return False


def install_driver(driver_inf_path: str) -> Tuple[bool, str]:
    """Install a driver from INF file"""
    try:
        cmd = f'pnputil /add-driver "{driver_inf_path}" /install'
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )

        success = result.returncode == 0
        message = result.stdout if success else result.stderr

        return success, message
    except Exception as e:
        logger.error(f"Error installing driver: {e}")
        return False, str(e)


def get_driver_store_info() -> Dict:
    """Get information about the driver store"""
    try:
        ps_script = """
        $driverStore = Get-WindowsDriver -Online

        @{
            TotalDrivers = $driverStore.Count
            BootCritical = ($driverStore | Where-Object {$_.BootCritical -eq $true}).Count
            InBox = ($driverStore | Where-Object {$_.ClassName -eq "Inbox"}).Count
        } | ConvertTo-Json
        """

        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
        return {}
    except Exception as e:
        logger.error(f"Error getting driver store info: {e}")
        return {}


def check_disk_space(required_gb: float = 1.0) -> Tuple[bool, float]:
    """Check if there's enough disk space for driver downloads"""
    try:
        import shutil

        # Get free space on system drive
        stats = shutil.disk_usage(os.getenv('SystemDrive', 'C:'))
        free_gb = stats.free / (1024**3)

        has_space = free_gb >= required_gb
        return has_space, free_gb
    except Exception as e:
        logger.error(f"Error checking disk space: {e}")
        return False, 0.0


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_date(date_str: str) -> str:
    """Format date string to readable format"""
    try:
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                dt = datetime.strptime(date_str.split()[0], fmt)
                return dt.strftime('%d %b %Y')
            except ValueError:
                continue
        return date_str
    except:
        return date_str


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings
    Returns: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
    """
    try:
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]

        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))

        for a, b in zip(v1_parts, v2_parts):
            if a > b:
                return 1
            elif a < b:
                return -1
        return 0
    except:
        return 0


def cleanup_temp_files(temp_dir: str = None):
    """Clean up temporary driver files"""
    try:
        import shutil

        if temp_dir is None:
            temp_dir = os.path.join(os.environ.get('TEMP', ''), 'driver_checker')

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: {temp_dir}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")
        return False


def get_network_adapters() -> List[Dict]:
    """Get network adapter information"""
    try:
        ps_script = """
        Get-NetAdapter |
        Select-Object Name, InterfaceDescription, Status, MacAddress, LinkSpeed, DriverVersion |
        ConvertTo-Json
        """

        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout:
            adapters = json.loads(result.stdout)
            if isinstance(adapters, dict):
                adapters = [adapters]
            return adapters
        return []
    except Exception as e:
        logger.error(f"Error getting network adapters: {e}")
        return []


def get_graphics_info() -> List[Dict]:
    """Get graphics card and driver information"""
    try:
        ps_script = """
        Get-WmiObject Win32_VideoController |
        Select-Object Name, DriverVersion, DriverDate, VideoProcessor, AdapterRAM, Status |
        ConvertTo-Json
        """

        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout:
            cards = json.loads(result.stdout)
            if isinstance(cards, dict):
                cards = [cards]
            return cards
        return []
    except Exception as e:
        logger.error(f"Error getting graphics info: {e}")
        return []


if __name__ == "__main__":
    # Test utilities
    print("=== Testing Driver Utilities ===\n")

    print("1. Admin Check:")
    print(f"   Running as admin: {is_admin()}\n")

    print("2. System Info:")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        print(f"   {key}: {value}")
    print()

    print("3. Windows Update Service:")
    print(f"   Service running: {check_windows_update_service()}\n")

    print("4. Problematic Devices:")
    problems = get_problematic_devices()
    print(f"   Found {len(problems)} device(s) with problems")
    for device in problems[:3]:
        print(f"   - {device.get('Name', 'Unknown')}")
    print()

    print("5. Disk Space:")
    has_space, free_gb = check_disk_space()
    print(f"   Free space: {free_gb:.2f} GB")
    print(f"   Has enough space: {has_space}\n")

    print("6. Graphics Cards:")
    graphics = get_graphics_info()
    for card in graphics:
        print(f"   - {card.get('Name', 'Unknown')}")
        print(f"     Driver: {card.get('DriverVersion', 'N/A')}")
    print()

    print("Tests completed!")
