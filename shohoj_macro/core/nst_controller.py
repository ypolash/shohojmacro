import time
import requests
import pyautogui
from typing import Optional, Dict

class NSTController:
    """
    Dual-Strategy NST Browser Controller.
    Strategy A: API Mode (Fast, invisible, uses NST Local API)
    Strategy B: GUI Mode (Uses physical mouse/keyboard, fallback when API is unauthenticated or fails)
    """
    
    def __init__(self, api_key: str = None, local_url: str = None):
        from shohoj_macro.core.settings_manager import SettingsManager
        sm = SettingsManager()
        self.api_key = api_key if api_key is not None else sm.get("nst", "api_key", "")
        url = local_url if local_url is not None else sm.get("nst", "local_url", "http://localhost:8848")
        
        self.base_url = url.rstrip("/")
        if not self.base_url.endswith("/api/v2") and not self.base_url.endswith("/api/v1"):
            self.base_url = f"{self.base_url}/api/v2"
            
        self.headers = {"x-api-key": self.api_key} if self.api_key else {}
        self.last_launched_profile_id: Optional[str] = None
        
    def _is_api_mode(self) -> bool:
        return bool(self.api_key or self.base_url)
        
    def prepare_and_launch(self, email: str, proxy_string: str = "") -> Optional[str]:
        """
        Main entry point. Finds profile by email, updates proxy if provided, and launches.
        Returns the webSocketDebuggerUrl if successful.
        """
        if not email:
            raise ValueError("Profile email/name cannot be empty.")
            
        try:
            ws_url = self._launch_via_api(email, proxy_string)
            if ws_url:
                return ws_url
        except Exception as api_err:
            from shohoj_macro.core.settings_manager import SettingsManager
            sm = SettingsManager()
            fallback = sm.get("nst", "enable_gui_fallback", True)
            if not fallback:
                raise api_err
            print(f"[NSTController] API launch error ({api_err}). Attempting GUI fallback...")
            return self._launch_via_gui(email, proxy_string)
            
        return None

    def stop_profile(self, profile_id: str = None) -> bool:
        """Stops/closes an active NST profile to prevent RAM and port accumulation."""
        target_id = profile_id or self.last_launched_profile_id
        if not target_id:
            return False
            
        stop_url = f"{self.base_url}/stop/{target_id}"
        try:
            res = requests.post(stop_url, headers=self.headers, timeout=3)
            if res.ok:
                print(f"[NSTController] Stopped profile {target_id}")
                if target_id == self.last_launched_profile_id:
                    self.last_launched_profile_id = None
                return True
        except Exception as e:
            print(f"[NSTController] Error stopping profile {target_id}: {e}")
        return False

    def find_running_browser_ws_url(self, exclude_port: Optional[int] = None) -> Optional[str]:
        """
        Ultra-fast (50ms) scanner for running NST/Chrome browser debugger endpoints.
        Uses native netstat on Windows to scan listening ports, with process fallback.
        """
        import subprocess
        import re

        candidate_ports = []

        # Strategy 1: Ultra-fast native netstat scan (takes 50ms)
        try:
            out = subprocess.check_output("netstat -ano -p tcp", shell=True, timeout=2).decode('utf-8', errors='ignore')
            for line in out.splitlines():
                if "LISTENING" in line and ("127.0.0.1:" in line or "[::1]:" in line):
                    m = re.search(r"127\.0\.0\.1:(\d+)", line)
                    if m:
                        p = int(m.group(1))
                        # Browser remote debugging ports are typically > 1024 and not standard services
                        if p > 1024 and p != 8848 and (exclude_port is None or p != exclude_port):
                            if p not in candidate_ports:
                                candidate_ports.append(p)
        except Exception:
            pass

        # Strategy 2: Fast check of candidate ports against /json/version
        for port in candidate_ports:
            try:
                res = requests.get(f"http://127.0.0.1:{port}/json/version", timeout=0.25)
                if res.ok:
                    data = res.json()
                    ws_url = data.get("webSocketDebuggerUrl")
                    if ws_url:
                        return ws_url
            except Exception:
                continue

        # Strategy 3: Fallback command-line scan if netstat didn't find it
        try:
            ps_cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_Process | Select-Object -ExpandProperty CommandLine"'
            output = subprocess.check_output(ps_cmd, shell=True, timeout=4).decode('utf-8', errors='ignore')
            ports = [int(p) for p in set(re.findall(r'--remote-debugging-port=(\d+)', output))]
            for port in ports:
                if exclude_port is not None and port == exclude_port:
                    continue
                try:
                    res = requests.get(f"http://127.0.0.1:{port}/json/version", timeout=0.5)
                    if res.ok:
                        ws_url = res.json().get("webSocketDebuggerUrl")
                        if ws_url:
                            return ws_url
                except Exception:
                    continue
        except Exception as e:
            print(f"[Auto-Detect] Fallback process scan error: {e}")

        return None
            
    def _launch_via_api(self, email: str, proxy_string: str) -> Optional[str]:
        """Strategy A: Use NST Local API."""
        import urllib.parse
        # 1. Search profile by email / name
        quoted_email = urllib.parse.quote(email)
        search_url = f"{self.base_url}/profiles?s={quoted_email}"
        try:
            res = requests.get(search_url, headers=self.headers, timeout=5)
            if not res.ok:
                raise Exception(f"HTTP {res.status_code} from NST API: {res.text}")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to NST Local API at '{self.base_url}'. Is NST Browser running?")
            
        data = res.json().get("data", {})
        docs = data.get("docs", [])
        if not docs:
            raise Exception(f"Profile not found for email: '{email}'")
            
        # Match exact name/email if multiple results returned
        matched_doc = None
        email_clean = email.strip().lower()
        for doc in docs:
            name = str(doc.get("name", "")).strip().lower()
            doc_email = str(doc.get("email", "")).strip().lower()
            if name == email_clean or doc_email == email_clean:
                matched_doc = doc
                break
        if not matched_doc:
            for doc in docs:
                name = str(doc.get("name", "")).strip().lower()
                doc_email = str(doc.get("email", "")).strip().lower()
                if email_clean in name or email_clean in doc_email:
                    matched_doc = doc
                    break
        if not matched_doc:
            matched_doc = docs[0]
            
        profile_id = matched_doc.get("profileId") or matched_doc.get("id") or matched_doc.get("_id")
        if not profile_id:
            raise Exception(f"Profile found for '{email}', but could not extract profileId from: {matched_doc}")
            
        self.last_launched_profile_id = profile_id
        
        # 2. Launch Profile via GET endpoint
        connect_url = f"{self.base_url}/connect/{profile_id}"
        conn_res = requests.get(connect_url, headers=self.headers, timeout=10)
        if not conn_res.ok:
            if conn_res.status_code in (401, 400) or "unauthorized" in conn_res.text.lower():
                raise Exception(f"NST API key required or invalid. Please enter your valid API key in Settings -> Proxy & Browser.")
            raise Exception(f"HTTP {conn_res.status_code} launching profile: {conn_res.text}")
            
        conn_data = conn_res.json().get("data", {})
        ws_url = conn_data.get("webSocketDebuggerUrl") or conn_data.get("ws")
        if not ws_url and conn_data.get("port"):
            ws_url = f"ws://127.0.0.1:{conn_data.get('port')}/devtools/browser"
            
        if not ws_url:
            raise Exception(f"NST profile launched but no webSocketDebuggerUrl was returned: {conn_res.text}")
            
        return ws_url
        
    def _launch_via_gui(self, email: str, proxy_string: str = "") -> Optional[str]:
        """
        Strategy B: Win32 Focus & Physical Mouse/Keyboard Search Fallback.
        """
        print(f"[GUI Mode] Searching for '{email}' in NST Browser window...")
        try:
            import win32gui
            import win32con
            
            hwnd = None
            def _enum_windows(h, _):
                nonlocal hwnd
                if win32gui.IsWindowVisible(h):
                    t = win32gui.GetWindowText(h)
                    if "NST" in t or "NstBrowser" in t:
                        hwnd = h
            win32gui.EnumWindows(_enum_windows, None)
            
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.4)
                pyautogui.hotkey("ctrl", "f")
                time.sleep(0.3)
                pyautogui.hotkey("ctrl", "a")
                pyautogui.press("backspace")
                pyautogui.write(email, interval=0.02)
                pyautogui.press("enter")
                time.sleep(1.0)
                
            return self.find_running_browser_ws_url()
        except Exception as e:
            print(f"[GUI Mode] Exception during visual fallback: {e}")
            return None

