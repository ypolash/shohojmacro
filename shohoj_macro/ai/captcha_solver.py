from playwright.sync_api import sync_playwright
import json
import time
import random
from typing import List
from shohoj_macro.ai.openrouter_client import OpenRouterClient
from shohoj_macro.core.cdp_spatial_bridge import CDPSpatialBridge
from shohoj_macro.core.humanizer import HumanizerEngine
from shohoj_macro.utils.win32_input import send_mouse_click
from shohoj_macro.core.stealth_core import StealthCore
from shohoj_macro.core.settings_manager import SettingsManager

class ReCaptchaSolver:
    """Solves reCAPTCHA v2 image grid challenges using CDP and OpenRouter."""
    
    def __init__(self, cdp_bridge: CDPSpatialBridge, ai_client: OpenRouterClient):
        self.cdp = cdp_bridge
        self.ai = ai_client
        self.humanizer_enabled = True
        self.settings = SettingsManager()
        
    def solve(self, max_rounds: int = None) -> bool:
        """
        Solves the captcha loop.
        Assumes the checkbox was already clicked and the challenge iframe is visible.
        """
        if not self.cdp.is_alive() or not self.cdp.ws_url:
            print("[CaptchaSolver] CDP connection not active.")
            return False
            
        rounds_to_run = max_rounds or self.settings.get("captcha", "max_retry_rounds", 4)
        print(f"[CaptchaSolver] Starting CAPTCHA solve loop. Max rounds: {rounds_to_run}")
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(self.cdp.ws_url)
            except Exception as e:
                print(f"[CaptchaSolver] CDP Connection error: {e}")
                return False
                
            try:
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                valid_pages = [page for page in context.pages if not page.url.startswith("chrome-extension://")]
                if not valid_pages:
                    print("[CaptchaSolver] No valid page found.")
                    return False
                page = valid_pages[-1]
                
                for round_idx in range(rounds_to_run):
                    time.sleep(2) # Wait for images to load
                    
                    # 1. Check if challenge is solved or still visible
                    challenge_frame = page.frame_locator("iframe[title*='recaptcha challenge']")
                    
                    if challenge_frame.count() == 0:
                        print("[CaptchaSolver] Challenge frame gone. Solved!")
                        return True
                        
                    # 2. Extract Instruction Text
                    instruction_element = challenge_frame.locator(".rc-imageselect-instructions").first
                    if instruction_element.count() == 0:
                        print("[CaptchaSolver] No instructions found. Waiting...")
                        time.sleep(2)
                        continue
                        
                    instruction_text = instruction_element.inner_text()
                    print(f"[CaptchaSolver] Instruction: {instruction_text}")
                    
                    # 3. Extract Image Grid
                    table_element = challenge_frame.locator("table.rc-imageselect-table").first
                    if table_element.count() == 0:
                        print("[CaptchaSolver] Grid not found.")
                        continue
                        
                    image_bytes = table_element.screenshot()
                    import base64
                    b64_image = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # 4. Ask AI
                    base_prompt = self.settings.get(
                        "captcha", 
                        "custom_prompt", 
                        "You are a CAPTCHA solver. The instruction is: '{instruction}'. This is a grid of images. The grid is numbered 1 to 9 from left to right, top to bottom. Which grid positions contain the target object? Return ONLY a JSON array of integers, for example: [1, 4, 7]."
                    )
                    prompt = base_prompt.replace("{instruction}", instruction_text)
                    
                    print("[CaptchaSolver] Asking AI for solution...")
                    try:
                        ai_response = self.ai.chat_with_images(prompt, [b64_image])
                        print(f"[CaptchaSolver] AI replied: {ai_response}")
                        
                        import re
                        match = re.search(r'\[(.*?)\]', ai_response)
                        if match:
                            indices_str = match.group(1).split(",")
                            indices = [int(i.strip()) for i in indices_str if i.strip().isdigit()]
                        else:
                            indices = []
                    except Exception as e:
                        print(f"[CaptchaSolver] AI Error: {e}")
                        indices = []
                        
                    print(f"[CaptchaSolver] Clicking indices: {indices}")
                    
                    # 5. Click the returned indices
                    if not indices:
                        print("[CaptchaSolver] AI returned no indices. Clicking Verify/Skip...")
                    else:
                        for idx in indices:
                            cells = table_element.locator("td")
                            count = cells.count()
                            
                            if 1 <= idx <= count:
                                cell = cells.nth(idx - 1)
                                box = cell.bounding_box()
                                if box:
                                    offset_x, offset_y = self.cdp.get_window_position()
                                    target_x = int(box['x'] + offset_x + (box['width'] / 2))
                                    target_y = int(box['y'] + offset_y + (box['height'] / 2))
                                    
                                    if self.humanizer_enabled:
                                        HumanizerEngine.move_humanized(
                                            target_x, target_y, duration_ms=130.0, curve_type="windmouse"
                                        )
                                    
                                    hold_ms = StealthCore.calculate_human_click_hold_ms() if self.humanizer_enabled else 45.0
                                    send_mouse_click("left", hold_ms=hold_ms)
                                    time.sleep(random.uniform(0.3, 0.7))
                                    
                    # 6. Click Verify / Next
                    verify_button = challenge_frame.locator("#recaptcha-verify-button").first
                    if verify_button.count() > 0:
                        box = verify_button.bounding_box()
                        if box:
                            offset_x, offset_y = self.cdp.get_window_position()
                            target_x = int(box['x'] + offset_x + (box['width'] / 2))
                            target_y = int(box['y'] + offset_y + (box['height'] / 2))
                            
                            if self.humanizer_enabled:
                                HumanizerEngine.move_humanized(target_x, target_y, duration_ms=120.0, curve_type="windmouse")
                                
                            hold_ms = StealthCore.calculate_human_click_hold_ms() if self.humanizer_enabled else 45.0
                            send_mouse_click("left", hold_ms=hold_ms)
                            
                print("[CaptchaSolver] Failed to solve CAPTCHA within max rounds.")
                return False
            finally:
                browser.close()
