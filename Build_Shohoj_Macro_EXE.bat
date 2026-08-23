@echo off
title Build Shohoj Macro EXE - Polash Khan (ypolash2)
cd /d "%~dp0"
echo ==================================================
echo   Building Shohoj Macro Standalone Executable
echo   Developer: Polash Khan (ypolash2)
echo ==================================================
echo.
python build_exe.py
echo.
pause
