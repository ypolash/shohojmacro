"""
Shohoj Macro - Release Packaging Utility
Creates clean, portable .zip distribution bundles for GitHub Releases.
"""

import os
import shutil
import zipfile

def make_release_zips():
    print("==================================================")
    print("  Creating Shohoj Macro v2.0.0 Release Packages...")
    print("==================================================")

    os.makedirs("releases", exist_ok=True)

    # 1. Package Standalone Windows App
    app_dist_dir = "dist/ShohojMacro"
    app_zip_path = "releases/ShohojMacro-v2.0.0-Windows-x64.zip"

    if os.path.exists(app_dist_dir):
        print(f"[*] Compressing Standalone Windows App from '{app_dist_dir}'...")
        with zipfile.ZipFile(app_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(app_dist_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, "dist")
                    zipf.write(file_path, arcname)
        print(f"[+] Created: {app_zip_path} ({os.path.getsize(app_zip_path) / (1024*1024):.2f} MB)")
    else:
        print("[!] dist/ShohojMacro not found. Run build_exe.py first.")

    # 2. Package Browser Companion Extension
    ext_dir = "browser_extension"
    ext_zip_path = "releases/ShohojCompanion-Extension-v2.0.0.zip"

    if os.path.exists(ext_dir):
        print(f"[*] Compressing Browser Companion Extension from '{ext_dir}'...")
        with zipfile.ZipFile(ext_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(ext_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, ".")
                    zipf.write(file_path, arcname)
        print(f"[+] Created: {ext_zip_path} ({os.path.getsize(ext_zip_path) / 1024:.2f} KB)")

    print("\n[SUCCESS] Release packages created in /releases folder!")

if __name__ == "__main__":
    make_release_zips()
