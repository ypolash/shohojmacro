from typing import Dict, Tuple, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
import socket
import json
import base64
import os
import requests

def _raw_ws_eval(ws_url: str, js_code: str):
    """Executes JS directly on a target WebSocket via raw TCP, completely bypassing OOPIF/Playwright restrictions."""
    try:
        if not ws_url: return None
        port = ws_url.split(":")[2].split("/")[0]
        path = "/" + ws_url.split("/", 3)[-1]
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.5)
        s.connect(("127.0.0.1", int(port)))
        
        sec_key = base64.b64encode(os.urandom(16)).decode('utf-8')
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {sec_key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(req.encode('utf-8'))
        resp = s.recv(1024).decode('utf-8', errors='ignore')
        if "101" not in resp:
            s.close()
            return None
            
        msg = json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": js_code,
                "returnByValue": True,
                "awaitPromise": True
            }
        })
        
        data = msg.encode('utf-8')
        length = len(data)
        frame = bytearray()
        frame.append(0x81)
        mask_key = os.urandom(4)
        if length <= 125:
            frame.append(0x80 | length)
        elif length <= 65535:
            frame.append(0x80 | 126)
            frame.extend(length.to_bytes(2, byteorder='big'))
        else:
            frame.append(0x80 | 127)
            frame.extend(length.to_bytes(8, byteorder='big'))
        frame.extend(mask_key)
        masked_data = bytearray(length)
        for i in range(length):
            masked_data[i] = data[i] ^ mask_key[i % 4]
        frame.extend(masked_data)
        
        s.sendall(bytes(frame))
        
        b1, b2 = s.recv(1), s.recv(1)
        if not b1 or not b2:
            s.close()
            return None
        l = b2[0] & 0x7F
        if l == 126:
            l = int.from_bytes(s.recv(2), byteorder='big')
        elif l == 127:
            l = int.from_bytes(s.recv(8), byteorder='big')
        is_masked = bool(b2[0] & 0x80)
        if is_masked:
            mask_key = s.recv(4)
        payload = bytearray()
        while len(payload) < l:
            chunk = s.recv(l - len(payload))
            if not chunk: break
            payload.extend(chunk)
        if is_masked:
            for i in range(l): payload[i] ^= mask_key[i % 4]
            
        s.close()
        res_json = json.loads(payload.decode('utf-8', errors='ignore'))
        return res_json.get("result", {}).get("result", {}).get("value")
    except Exception:
        return None

def _raw_ws_eval_all_targets(base_ws_url: str, js_code: str):
    """Fetches all targets from /json/list and evaluates JS on each page/iframe target via raw WS."""
    if not base_ws_url:
        return []
    try:
        port = base_ws_url.split(":")[2].split("/")[0]
        res = requests.get(f"http://127.0.0.1:{port}/json/list", timeout=1.0)
        if not res.ok:
            return []
        targets = res.json()
        results = []
        found_boolean = False
        for t in targets:
            ws_url = t.get("webSocketDebuggerUrl")
            if not ws_url or t.get("type") not in ("page", "iframe"):
                continue
            val = _raw_ws_eval(ws_url, js_code)
            if val is True:
                found_boolean = True
            elif isinstance(val, list):
                results.extend(val)
            elif isinstance(val, dict):
                results.append(val)
        if found_boolean:
            return True
        return results
    except Exception:
        return []

class CDPSpatialBridge:
    """
    Connects to a running NST browser via Chrome DevTools Protocol (CDP) WebSocket.
    Acts as a DOM Inspector to find exact physical screen coordinates of elements,
    so the macro can physically click them without synthetic JS events.
    Stateless implementation to avoid Tkinter greenlet thread crashes.
    """
    
    def __init__(self):
        self._connected = False
        self.ws_url = None
        
    def connect(self, ws_url: str):
        self.ws_url = ws_url
        self._connected = True
        print(f"[CDP Bridge] Configured for WS URL: {ws_url}")
        
    def disconnect(self):
        self.ws_url = None
        self._connected = False
        
    def is_alive(self) -> bool:
        if not self.ws_url:
            return False
        import urllib.parse
        try:
            parsed = urllib.parse.urlparse(self.ws_url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 9222
            with socket.create_connection((host, port), timeout=2.0):
                self._connected = True
                return True
        except Exception:
            return False

    def _connect_cdp(self, p):
        if not self.ws_url:
            raise ConnectionError("CDP Bridge not connected.")
        try:
            return p.chromium.connect_over_cdp(self.ws_url, timeout=5000)
        except Exception as e:
            raise ConnectionError(f"CDP connection refused at {self.ws_url}: {e}")

    def evaluate_js(self, js_code: str):
        with sync_playwright() as p:
            browser = self._connect_cdp(p)
            try:
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                valid_pages = [page for page in context.pages if not page.url.startswith("chrome-extension://")]
                page = valid_pages[-1] if valid_pages else context.new_page()
                return page.evaluate(js_code)
            finally:
                browser.close()

    def evaluate_js_all_frames(self, js_code: str):
        """Runs JS across Playwright frames AND raw CDP targets (for OOPIF cross-origin iframes)."""
        aggregated_elements = []
        found_boolean = False
        title = ""
        url = ""
        
        # 1. Playwright pass
        try:
            with sync_playwright() as p:
                browser = self._connect_cdp(p)
                try:
                    context = browser.contexts[0] if browser.contexts else browser.new_context()
                    valid_pages = [page for page in context.pages if not page.url.startswith("chrome-extension://")]
                    page = valid_pages[-1] if valid_pages else context.new_page()
                    url = page.url
                    try: title = page.title()
                    except Exception: pass
                    
                    frames_to_check = []
                    for f in page.frames:
                        try:
                            if not f.is_detached(): frames_to_check.append(f)
                        except Exception: pass
                    if not frames_to_check: frames_to_check = [page]
                    
                    for frame in frames_to_check:
                        try:
                            res = frame.evaluate(js_code)
                            if res is True: found_boolean = True
                            elif isinstance(res, list): aggregated_elements.extend(res)
                            elif isinstance(res, dict):
                                if "elements" in res: aggregated_elements.extend(res.get("elements", []))
                                else: aggregated_elements.append(res)
                        except Exception: pass
                finally:
                    browser.close()
        except Exception as e:
            print(f"[CDP Bridge] Playwright pass error: {e}")

        # 2. Raw CDP targets pass (for cross-origin OOPIFs missed by Playwright)
        try:
            raw_res = _raw_ws_eval_all_targets(self.ws_url, js_code)
            if raw_res is True:
                found_boolean = True
            elif isinstance(raw_res, list):
                existing_selectors = {el.get("selector") for el in aggregated_elements if isinstance(el, dict) and el.get("selector")}
                for item in raw_res:
                    if isinstance(item, dict):
                        sel = item.get("selector")
                        if not sel or sel not in existing_selectors:
                            aggregated_elements.append(item)
                            if sel: existing_selectors.add(sel)
        except Exception as e:
            print(f"[CDP Bridge] Raw CDP pass error: {e}")

        if found_boolean:
            return True
        return {"title": title, "url": url, "elements": aggregated_elements}

    def navigate(self, url: str):
        if not self.ws_url: return
        with sync_playwright() as p:
            browser = self._connect_cdp(p)
            try:
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                valid_pages = [page for page in context.pages if not page.url.startswith("chrome-extension://")]
                page = valid_pages[-1] if valid_pages else context.new_page()
                try: page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e: print(f"[CDP Bridge] Navigation timeout/error (ignoring): {e}")
            finally:
                browser.close()
                
    def wait_for_idle(self, timeout_ms: int = 5000):
        if not self.ws_url: return
        with sync_playwright() as p:
            browser = self._connect_cdp(p)
            try:
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                valid_pages = [page for page in context.pages if not page.url.startswith("chrome-extension://")]
                page = valid_pages[-1] if valid_pages else context.new_page()
                try: page.wait_for_load_state("networkidle", timeout=timeout_ms)
                except Exception: pass
            finally:
                browser.close()

    def perform_action(self, selector: str, text: Optional[str] = None, error_policy: str = "stop", timeout_ms: int = 3000) -> bool:
        if not self.ws_url:
            raise ConnectionError("CDP Bridge not connected.")

        safe_selector = json.dumps(selector)

        # 1. Try Playwright locators
        pw_success = False
        try:
            with sync_playwright() as p:
                browser = self._connect_cdp(p)
                try:
                    context = browser.contexts[0] if browser.contexts else browser.new_context()
                    valid_pages = [page for page in context.pages if not page.url.startswith("chrome-extension://")]
                    if valid_pages:
                        page = valid_pages[-1]
                        target_frame = page
                        locator = page.locator(selector).first

                        is_present = False
                        max_wait = max(timeout_ms, 3000) / 1000.0
                        import time
                        start_time = time.time()

                        while time.time() - start_time < max_wait:
                            try:
                                floc = page.locator(selector).first
                                if floc.count() > 0:
                                    locator = floc
                                    target_frame = page
                                    is_present = True
                                    break
                            except Exception: pass

                            for frame in page.frames:
                                try:
                                    floc = frame.locator(selector).first
                                    if floc.count() > 0:
                                        locator = floc
                                        target_frame = frame
                                        is_present = True
                                        break
                                except Exception: pass

                            if is_present: break
                            time.sleep(0.3)

                        if is_present:
                            try: page.bring_to_front()
                            except Exception: pass
                            try: locator.scroll_into_view_if_needed(timeout=1500)
                            except Exception: pass

                            info = target_frame.evaluate(f"() => {{ let el = document.querySelector({safe_selector}); return el ? {{ tag: el.tagName.toLowerCase(), type: (el.type || '').toLowerCase() }} : null; }}") or {}
                            el_tag = info.get('tag', '')
                            el_type = info.get('type', '')
                            
                            if el_tag == "select":
                                if text:
                                    try: locator.select_option(label=text, timeout=2000)
                                    except Exception:
                                        try: locator.select_option(value=text, timeout=2000)
                                        except Exception: locator.select_option(index=1, timeout=2000)
                                else:
                                    locator.click(timeout=2000, force=True)
                            elif el_type == "checkbox":
                                try:
                                    if not locator.is_checked():
                                        locator.check(force=True, timeout=2000)
                                except Exception:
                                    locator.click(timeout=2000, force=True)
                            elif el_type == "radio":
                                try: locator.check(force=True, timeout=2000)
                                except Exception: locator.click(timeout=2000, force=True)
                            else:
                                if text is not None and text != "":
                                    locator.fill(text, timeout=2000, force=True)
                                else:
                                    locator.click(timeout=2000, force=True)
                            pw_success = True
                finally:
                    browser.close()
        except Exception as e:
            print(f"[CDP Bridge] Playwright action error: {e}")

        if pw_success:
            return True

        # 2. Raw CDP Fallback (for OOPIF cross-origin iframes missed by Playwright)
        print(f"[CDP Bridge] Attempting raw CDP fallback for selector: {selector}")
        raw_js = f"""
        (() => {{
            let el = document.querySelector({safe_selector});
            if (!el && {safe_selector}.includes('#')) {{
                let cleanId = {safe_selector}.replace(/.*#/, '').replace(/\\\\\\\\/g, '');
                el = document.getElementById(cleanId);
            }}
            if (!el) return false;
            try {{ el.scrollIntoView({{ behavior: 'smooth', block: 'center' }}); }} catch(e) {{}}
            el.focus();
            let text = {json.dumps(text)};
            
            if (text !== null && text !== undefined && text !== '') {{
                let tag = el.tagName.toLowerCase();
                if (tag === 'select') {{
                    let opts = Array.from(el.options);
                    let lowerText = text.trim().toLowerCase();
                    let targetOpt = null;
                    
                    if (lowerText.includes('1st') || lowerText.includes('first')) {{
                        targetOpt = opts.find(o => o.index === 1) || opts[1];
                    }} else if (lowerText.includes('2nd') || lowerText.includes('second')) {{
                        targetOpt = opts.find(o => o.index === 2) || opts[2];
                    }}
                    
                    if (!targetOpt) {{
                        targetOpt = opts.find(o => (o.text || '').trim() === text || o.value === text);
                    }}
                    if (!targetOpt) {{
                        targetOpt = opts.find(o => (o.text || '').trim().toLowerCase() === lowerText);
                    }}
                    if (!targetOpt) {{
                        targetOpt = opts.find(o => {{
                            let t = (o.text || '').trim().toLowerCase();
                            return t.startsWith(lowerText) || lowerText.startsWith(t) || t.includes(lowerText) || lowerText.includes(t);
                        }});
                    }}
                    
                    if (targetOpt) {{
                        el.value = targetOpt.value;
                        targetOpt.selected = true;
                    }} else {{
                        el.value = text;
                    }}
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }} else {{
                    el.value = text;
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            }} else {{
                if (el.type === 'checkbox') {{
                    if (!el.checked) {{
                        el.click();
                        if (!el.checked) {{
                            el.checked = true;
                            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    }}
                }} else if (el.type === 'radio') {{
                    if (!el.checked) {{
                        el.click();
                        if (!el.checked) {{
                            el.checked = true;
                            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    }}
                }} else {{
                    el.click();
                    if (el.form && (el.type === 'submit' || (el.className || '').includes('submit') || (el.value || '').toLowerCase().includes('submit'))) {{
                        try {{ el.form.requestSubmit(); }} catch(e) {{ try {{ el.form.submit(); }} catch(err) {{}} }}
                    }}
                }}
            }}
            return true;
        }})()
        """
        raw_res = _raw_ws_eval_all_targets(self.ws_url, raw_js)
        if raw_res is True:
            print(f"[CDP Bridge] Raw CDP action SUCCEEDED for selector: {selector}")
            return True

        is_optional = (error_policy == "skip") or any(
            term in selector.lower() for term in ["onetrust", "cookie", "consent", "gdpr", "modal", "alert-box"]
        )
        if is_optional:
            print(f"[CDP Bridge] Optional element '{selector}' not present. Skipping.")
            return True

        raise Exception(f"CDP Element '{selector}' not found on page or cross-origin iframes.")
