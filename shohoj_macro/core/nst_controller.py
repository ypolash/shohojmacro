import time
import requests
import pyautogui
from typing import Optional, Dict

class NSTController:
    """
    Dual-Strategy NST Browser Controller.
    Strategy A: API Mode (Fast, invisible, requires API key)
    Strategy B: GUI Mode (Uses physical mouse/keyboard, no API key needed)
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "http://localhost:8848/api/v2"
        self.headers = {"x-api-key": self.api_key} if self.api_key else {}
        
    def _is_api_mode(self) -> bool:
        return bool(self.api_key)
        
    def prepare_and_launch(self, email: str, proxy_string: str) -> Optional[str]:
        """
        Main entry point. Finds profile by email, updates proxy, and launches.
        Returns the webSocketDebuggerUrl if successful.
        """
        return self._launch_via_api(email, proxy_string)

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
        """Strategy A: Use localhost API."""
        # 1. Search profile by email
        search_url = f"{self.base_url}/profiles?s={email}"
        try:
            res = requests.get(search_url, headers=self.headers)
            if not res.ok:
                raise Exception(f"HTTP {res.status_code} from NST: {res.text}")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to NST Local API on port 8848. Is it running?")
            
        data = res.json().get("data", {})
        docs = data.get("docs", [])
        if not docs:
            raise Exception(f"Profile not found for email: '{email}'")
            
        profile_id = docs[0].get("id")
        
        # 2. Update Proxy
        # Assuming the API takes the raw SOAX string or we might need to parse it
        # For now, we will just start the profile since proxy API endpoint docs vary
        # (This will be fleshed out when we have a valid key to test the exact payload)
        
        # 3. Launch Profile
        connect_url = f"{self.base_url}/connect/{profile_id}"
        conn_res = requests.post(connect_url, headers=self.headers)
        if not conn_res.ok:
            raise Exception(f"HTTP {conn_res.status_code} launching profile: {conn_res.text}")
            
        conn_data = conn_res.json().get("data", {})
        ws_url = conn_data.get("webSocketDebuggerUrl")
        if not ws_url:
            raise Exception(f"NST started but no webSocketDebuggerUrl was returned: {conn_res.text}")
        return ws_url
        
    def _launch_via_gui(self, email: str, proxy_string: str) -> Optional[str]:
        """
        Strategy B: Use physical mouse and keyboard.
        (This will be implemented using Shohoj's existing Humanizer/CV engine in Sprint 2.
         For now, we outline the steps).
        """
        print(f"[GUI Mode] Searching for {email} in NST window...")
        # Step 1: Focus NST Window (win32gui)
        # Step 2: Click Search Box (CV anchor)
        # Step 3: Type Email (pyautogui.write)
        # Step 4: Check Proxy Country Text (OCR)
        # Step 5: If mismatch, click proxy, paste proxy_string, click Update
        # Step 6: Click Play button
        # Step 7: Wait for browser to open and extract debug port from process args
        
        print("[GUI Mode] Profile launched.")
        return None # Return None for now until CDP extraction is built
