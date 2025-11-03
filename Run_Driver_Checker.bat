@echo off
REM Windows Driver Checker & Auto-Updater Launcher
REM This script will launch the driver checker with proper settings

echo =========================================
echo  Windows Driver Checker ^& Auto-Updater
echo =========================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running as Administrator
    echo.
) else (
    echo [WARNING] NOT running as Administrator!
    echo.
    echo For full functionality, please:
    echo 1. Right-click this file
    echo 2. Select "Run as Administrator"
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Python is installed
    python --version
    echo.
) else (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Run the application
echo Starting Driver Checker...
echo.
python windows_driver_checker.py

REM If there was an error
if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Application exited with error code: %errorLevel%
    echo.
    echo Check driver_checker.log for details.
    echo.
)

echo.
echo Application closed.
pause
