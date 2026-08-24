@echo off
title Shohoj Macro - Installing Requirements
color 0b
echo ======================================================================
echo           Shohoj Macro - Dependency Installer
echo           Developed by Polash Khan (ypolash)
echo ======================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Python is not installed or not found in system PATH.
    echo Please install Python 3.11+ from https://www.python.org/
    echo and ensure "Add python.exe to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

echo [*] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [*] Installing Shohoj Macro required libraries from requirements.txt...
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    color 0a
    echo ======================================================================
    echo  [SUCCESS] All dependencies have been installed successfully!
    echo  You can now run Launch_Shohoj_Macro.bat or python main.py
    echo ======================================================================
) else (
    echo.
    color 0c
    echo [!] Some packages failed to install. Please review the errors above.
)

echo.
pause
