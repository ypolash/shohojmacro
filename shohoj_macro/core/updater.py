import threading
import requests
import re
import os
import sys
import subprocess
import tempfile
from typing import Optional, Dict, Any, Callable
from shohoj_macro.version import __version__, __github__, __repo__

def parse_version_tuple(v_str: str) -> tuple:
    """Parses a version string like 'v2.5.0' or '2.5.0' into a numeric tuple (2, 5, 0)."""
    clean = re.sub(r'[^0-9.]', '', v_str)
    parts = [int(p) for p in clean.split('.') if p.isdigit()]
    return tuple(parts)

class UpdateChecker:
    """
    Remote Update Checker for Shohoj Macro.
    Queries GitHub Releases API to detect new version releases,
    notifies the user via GUI dialogs, and supports one-click updates.
    """
    
    API_URL = "https://api.github.com/repos/ypolash/shohojmacro/releases/latest"
    ATOM_URL = "https://github.com/ypolash/shohojmacro/releases.atom"

    @classmethod
    def check_for_updates_async(cls, on_result: Callable[[Optional[Dict[str, Any]]], None]):
        """Runs the update check in a background thread to prevent UI freezing."""
        def run():
            info = cls.check_for_updates_sync()
            on_result(info)
            
        t = threading.Thread(target=run, daemon=True)
        t.start()

    @classmethod
    def _fetch_via_atom_feed(cls) -> Optional[Dict[str, Any]]:
        """Fallback updater method using GitHub CDN Atom Feed (zero rate limits)."""
        import xml.etree.ElementTree as ET
        try:
            headers = {"User-Agent": f"ShohojMacro-Updater/{__version__}"}
            res = requests.get(cls.ATOM_URL, headers=headers, timeout=5.0)
            if not res.ok:
                return None
            root = ET.fromstring(res.text)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)
            if not entries:
                return None
            latest = entries[0]
            id_elem = latest.find('atom:id', ns)
            title_elem = latest.find('atom:title', ns)
            if id_elem is None or not id_elem.text:
                return None
            latest_tag = id_elem.text.strip().split('/')[-1]
            title = title_elem.text if title_elem is not None else f"Shohoj Macro {latest_tag}"
            
            current_ver = parse_version_tuple(__version__)
            latest_ver = parse_version_tuple(latest_tag)
            if latest_ver > current_ver:
                download_url = f"{__repo__}/releases/download/{latest_tag}/ShohojMacro-{latest_tag}-Windows-x64.zip"
                return {
                    "version": latest_tag.lstrip("v"),
                    "tag_name": latest_tag,
                    "title": title,
                    "html_url": f"{__repo__}/releases/tag/{latest_tag}",
                    "download_url": download_url,
                    "changelog": f"Shohoj Macro {latest_tag} Release",
                    "published_at": ""
                }
        except Exception as e:
            print(f"[UpdateChecker] Atom feed fallback failed: {e}")
        return None

    @classmethod
    def check_for_updates_sync(cls) -> Optional[Dict[str, Any]]:
        """Queries GitHub API synchronously. Returns update dict if a newer version is available."""
        try:
            headers = {"User-Agent": f"ShohojMacro-Updater/{__version__}"}
            res = requests.get(cls.API_URL, headers=headers, timeout=5.0)
            if not res.ok:
                print(f"[UpdateChecker] GitHub REST API returned HTTP {res.status_code}. Attempting Atom feed fallback...")
                return cls._fetch_via_atom_feed()
                
            data = res.json()
            latest_tag = data.get("tag_name", "")
            if not latest_tag:
                return cls._fetch_via_atom_feed()
                
            current_ver = parse_version_tuple(__version__)
            latest_ver = parse_version_tuple(latest_tag)
            
            if latest_ver > current_ver:
                # Find zip download asset
                download_url = None
                assets = data.get("assets", [])
                for asset in assets:
                    name = asset.get("name", "")
                    if name.endswith(".zip") and "ShohojMacro" in name:
                        download_url = asset.get("browser_download_url")
                        break
                        
                if not download_url:
                    download_url = f"{__repo__}/releases/download/{latest_tag}/ShohojMacro-{latest_tag}-Windows-x64.zip"
                    
                return {
                    "version": latest_tag.lstrip("v"),
                    "tag_name": latest_tag,
                    "title": data.get("name") or f"Shohoj Macro {latest_tag}",
                    "html_url": data.get("html_url") or f"{__repo__}/releases/tag/{latest_tag}",
                    "download_url": download_url,
                    "changelog": data.get("body", "").strip(),
                    "published_at": data.get("published_at", "")
                }
        except Exception as e:
            print(f"[UpdateChecker] Check failed: {e}. Trying Atom feed fallback...")
            return cls._fetch_via_atom_feed()
            
        return None

    @classmethod
    def trigger_auto_update(cls, download_url: str, app_dir: Optional[str] = None):
        """Downloads the new release zip and executes the background batch updater."""
        if not app_dir:
            app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(".")
            
        temp_dir = tempfile.gettempdir()
        zip_path = os.path.join(temp_dir, "shohoj_update.zip")
        bat_path = os.path.join(temp_dir, "apply_shohoj_update.bat")
        
        # Download ZIP
        print(f"[UpdateChecker] Downloading update from {download_url}...")
        res = requests.get(download_url, stream=True, timeout=30.0)
        res.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)
                
        # Write updater script
        bat_script = f"""@echo off
title Updating Shohoj Macro...
echo Waiting for Shohoj Macro to close...
timeout /t 2 /nobreak > NUL
echo Extracting update to {app_dir}...
powershell -NoProfile -Command "Expand-Archive -Path '{zip_path}' -DestinationPath '{app_dir}' -Force"
echo Launching updated Shohoj Macro...
start "" "{os.path.join(app_dir, 'ShohojMacro.exe')}"
del "{zip_path}"
(goto) 2>nul & del "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_script)
            
        # Launch updater batch file and quit app
        subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        sys.exit(0)
