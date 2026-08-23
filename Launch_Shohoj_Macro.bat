@echo off
title Shohoj Macro Studio - Polash Khan (ypolash2)
cd /d "%~dp0"

if exist "dist\ShohojMacro\ShohojMacro.exe" (
    start "" "dist\ShohojMacro\ShohojMacro.exe"
) else (
    python main.py
)
