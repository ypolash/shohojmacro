"""
Automated EXE Builder for Shohoj Macro
Packages the entire application into a standalone Windows Executable with assets and custom icon.
"""

import os
import sys
import subprocess
import shutil
import customtkinter

def build_executable():
    print("==================================================")
    print("  Building Shohoj Macro Standalone Executable...")
    print("  Developed by Polash Khan (ypolash2)")
    print("==================================================")

    # 1. Locate CustomTkinter directory to bundle theme json and assets
    ctk_dir = os.path.dirname(customtkinter.__file__)
    print(f"[+] CustomTkinter path: {ctk_dir}")

    # 2. Check icon
    icon_path = os.path.abspath("assets/icon.ico")
    if not os.path.exists(icon_path):
        from generate_icon import create_app_icon
        create_app_icon()

    # 3. Construct PyInstaller command
    dist_build_dir = os.path.abspath("dist_build")
    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath", dist_build_dir,
        "--onedir",                # Single folder distribution (fast startup, zero DLL extraction lag)
        "--windowed",              # No terminal console pop-up
        "--name", "ShohojMacro",
        "--icon", icon_path,
        # Add custom tkinter data folder
        "--add-data", f"{ctk_dir};customtkinter",
        # Add assets folder
        "--add-data", "assets;assets",
        # Collect all shohoj_macro modules
        "--collect-all", "shohoj_macro",
        # Hidden imports
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "pynput",
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.mouse._win32",
        "--hidden-import", "cv2",
        "--hidden-import", "numpy",
        "--hidden-import", "customtkinter",
        "--hidden-import", "openpyxl",
        "--hidden-import", "shohoj_macro",
        "--hidden-import", "shohoj_macro.ai",
        "--hidden-import", "shohoj_macro.core",
        "--hidden-import", "shohoj_macro.gui",
        "--hidden-import", "shohoj_macro.utils",
        # Entry point
        "main.py"
    ]

    print(f"[+] Running PyInstaller command:\n{' '.join(pyinstaller_cmd)}\n")
    result = subprocess.run(pyinstaller_cmd)

    if result.returncode == 0:
        target_dist = os.path.abspath("dist/ShohojMacro")
        src_dist = os.path.join(dist_build_dir, "ShohojMacro")
        print(f"[*] Copying build output from {src_dist} to {target_dist}...")
        try:
            shutil.copytree(src_dist, target_dist, dirs_exist_ok=True)
        except Exception as copy_err:
            print(f"[!] Warning copying to dist: {copy_err}")
            
        print("\n==================================================")
        print("  [SUCCESS] Shohoj Macro Executable built!")
        exe_path = os.path.join(target_dist, "ShohojMacro.exe")
        print(f"  Executable location: {exe_path}")
        print("==================================================")
        return True
    else:
        print(f"\n[!] Build failed with exit code {result.returncode}")
        return False

if __name__ == "__main__":
    build_executable()
