"""
Test Script for Windows Driver Checker
Run this to test all components before using the main application
"""

import sys
import subprocess
import platform


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_result(test_name, success, message=""):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} - {test_name}")
    if message:
        print(f"      {message}")


def test_platform():
    """Test if running on Windows"""
    print_header("Platform Check")
    is_windows = platform.system() == 'Windows'
    print_result(
        "Windows OS",
        is_windows,
        f"Detected: {platform.system()} {platform.release()}"
    )
    return is_windows


def test_python_version():
    """Test Python version"""
    print_header("Python Version Check")
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 7
    print_result(
        "Python 3.7+",
        is_valid,
        f"Current: {version.major}.{version.minor}.{version.micro}"
    )
    return is_valid


def test_admin_privileges():
    """Test admin privileges"""
    print_header("Administrator Privileges")
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print_result(
            "Running as Administrator",
            is_admin,
            "Required for full functionality" if not is_admin else "OK"
        )
        return is_admin
    except:
        print_result("Admin Check", False, "Unable to determine")
        return False


def test_tkinter():
    """Test tkinter availability"""
    print_header("GUI Library (tkinter)")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.destroy()
        print_result("tkinter", True, "GUI library available")
        return True
    except Exception as e:
        print_result("tkinter", False, f"Error: {str(e)}")
        return False


def test_powershell():
    """Test PowerShell availability"""
    print_header("PowerShell")
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Write-Output "Test"'],
            capture_output=True,
            text=True,
            timeout=10
        )
        success = result.returncode == 0
        print_result("PowerShell", success, "PowerShell is available")
        return success
    except Exception as e:
        print_result("PowerShell", False, f"Error: {str(e)}")
        return False


def test_windows_update_api():
    """Test Windows Update API access"""
    print_header("Windows Update API")
    try:
        ps_script = """
        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
        Write-Output "OK"
        """

        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        success = result.returncode == 0 and "OK" in result.stdout
        print_result(
            "Windows Update COM API",
            success,
            "Can access Windows Update services" if success else "Access denied or not available"
        )
        return success
    except Exception as e:
        print_result("Windows Update API", False, f"Error: {str(e)}")
        return False


def test_dism():
    """Test DISM availability"""
    print_header("DISM (Deployment Image Servicing)")
    try:
        result = subprocess.run(
            ['dism', '/?'],
            capture_output=True,
            text=True,
            timeout=10
        )
        success = result.returncode == 0
        print_result("DISM", success, "Driver scanning available")
        return success
    except Exception as e:
        print_result("DISM", False, f"Error: {str(e)}")
        return False


def test_wmi():
    """Test WMI access"""
    print_header("WMI (Windows Management Instrumentation)")
    try:
        ps_script = "Get-WmiObject Win32_OperatingSystem | Select-Object Caption"
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        success = result.returncode == 0
        print_result("WMI", success, "Can query system information")
        return success
    except Exception as e:
        print_result("WMI", False, f"Error: {str(e)}")
        return False


def test_windows_update_service():
    """Test Windows Update service status"""
    print_header("Windows Update Service")
    try:
        result = subprocess.run(
            ['sc', 'query', 'wuauserv'],
            capture_output=True,
            text=True,
            timeout=10
        )

        is_running = 'RUNNING' in result.stdout
        print_result(
            "Windows Update Service",
            True,  # Service existing is good enough
            "Running" if is_running else "Stopped (can be started automatically)"
        )
        return True
    except Exception as e:
        print_result("Windows Update Service", False, f"Error: {str(e)}")
        return False


def test_internet_connection():
    """Test internet connectivity"""
    print_header("Internet Connection")
    try:
        import urllib.request
        urllib.request.urlopen('http://www.microsoft.com', timeout=5)
        print_result("Internet", True, "Connected (needed for driver downloads)")
        return True
    except Exception as e:
        print_result("Internet", False, "No connection (some features may not work)")
        return False


def test_disk_space():
    """Test available disk space"""
    print_header("Disk Space")
    try:
        import shutil
        stats = shutil.disk_usage('C:\\')
        free_gb = stats.free / (1024**3)
        has_space = free_gb >= 1.0

        print_result(
            "Disk Space",
            has_space,
            f"Free: {free_gb:.2f} GB (need at least 1 GB)"
        )
        return has_space
    except Exception as e:
        print_result("Disk Space", False, f"Error: {str(e)}")
        return False


def test_modules():
    """Test if application modules can be imported"""
    print_header("Application Modules")

    modules = [
        ('windows_driver_checker', 'Main GUI application'),
        ('windows_update_api', 'Windows Update integration'),
        ('driver_utils', 'Utility functions')
    ]

    all_ok = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print_result(module_name, True, description)
        except Exception as e:
            print_result(module_name, False, f"Import error: {str(e)}")
            all_ok = False

    return all_ok


def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n✓ All tests passed! Application is ready to use.")
    elif not results.get('platform'):
        print("\n✗ CRITICAL: Not running on Windows. Application cannot run.")
    elif not results.get('python'):
        print("\n✗ CRITICAL: Python version too old. Please upgrade to 3.7+")
    else:
        print("\n⚠ Some tests failed. Application may have limited functionality.")

        if not results.get('admin'):
            print("  • Run as Administrator for full functionality")
        if not results.get('internet'):
            print("  • Connect to internet for driver downloads")
        if not results.get('windows_update_api'):
            print("  • Windows Update API not accessible (may need admin rights)")

    print("\n" + "=" * 60)


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Windows Driver Checker - System Test".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")

    results = {}

    # Critical tests
    results['platform'] = test_platform()
    if not results['platform']:
        print("\n⚠ This application only works on Windows!")
        return

    results['python'] = test_python_version()

    # System tests
    results['admin'] = test_admin_privileges()
    results['tkinter'] = test_tkinter()
    results['powershell'] = test_powershell()

    # API tests
    results['windows_update_api'] = test_windows_update_api()
    results['dism'] = test_dism()
    results['wmi'] = test_wmi()

    # Service tests
    results['windows_update_service'] = test_windows_update_service()

    # Resource tests
    results['internet'] = test_internet_connection()
    results['disk_space'] = test_disk_space()

    # Module tests
    results['modules'] = test_modules()

    # Print summary
    print_summary(results)

    # Recommendations
    if not results['admin']:
        print("\nRECOMMENDATION: Run this script as Administrator to unlock all features")
        print("  Right-click -> Run as Administrator")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
    finally:
        print("\nPress Enter to exit...")
        input()
