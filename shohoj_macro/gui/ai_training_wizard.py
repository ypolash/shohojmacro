import customtkinter as ctk
import threading
import json
import tkinter as tk
import tkinter.simpledialog as simpledialog
from typing import List, Tuple

from shohoj_macro.gui.glass_theme import GlassTheme, GlassButton
from shohoj_macro.ai.openrouter_client import OpenRouterClient
from shohoj_macro.core.cdp_spatial_bridge import CDPSpatialBridge
from shohoj_macro.core.nst_controller import NSTController
from shohoj_macro.core.events import MacroEvent, EventType, ErrorPolicy


class AITrainingWizard(ctk.CTkToplevel):
    def __init__(self, master, cdp_bridge: CDPSpatialBridge, nst_controller: NSTController, ai_client: OpenRouterClient, on_complete_callback):
        super().__init__(master)
        
        self.cdp = cdp_bridge
        self.nst = nst_controller
        self.ai = ai_client
        self.on_complete = on_complete_callback
        
        self.title("🧠 Agentic Co-Pilot Wizard")
        self.geometry("540x740")
        self.configure(fg_color=GlassTheme.BG_DARK)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        if master:
            self.update_idletasks()
            x = master.winfo_x() + (master.winfo_width() // 2) - (540 // 2)
            y = master.winfo_y() + (master.winfo_height() // 2) - (740 // 2)
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
            
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header Frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        lbl_header = ctk.CTkLabel(
            header_frame, 
            text="AI Co-Pilot: Text to Macro", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            text_color=GlassTheme.TEXT_PRIMARY
        )
        lbl_header.grid(row=0, column=0, sticky="w")
        
        self.lbl_status_badge = ctk.CTkLabel(
            header_frame, 
            text="🟢 Ready", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color=GlassTheme.ACCENT_EMERALD,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            corner_radius=6,
            padx=8,
            pady=2
        )
        self.lbl_status_badge.grid(row=0, column=1, sticky="e")
        
        # Quick Preset Pills Frame
        preset_frame = ctk.CTkFrame(self, fg_color="transparent")
        preset_frame.grid(row=1, column=0, padx=20, pady=(2, 5), sticky="ew")
        
        presets = [
            ("⚡ Auto-Form", "Extract and fill all form fields on this page with template variables"),
            ("🔑 Login", "Click username input, type {{Username}}, click password input, type {{Password}}, then click Login button"),
            ("🔍 Search & Click", "Type {{SearchTerm}} into the search field and press search button"),
        ]
        for idx, (label, p_text) in enumerate(presets):
            btn_p = ctk.CTkButton(
                preset_frame,
                text=label,
                font=ctk.CTkFont(size=11),
                fg_color=GlassTheme.CARD_BG_SECONDARY,
                text_color=GlassTheme.TEXT_PRIMARY,
                hover_color=GlassTheme.ACCENT_BLUE,
                height=24,
                corner_radius=12,
                command=lambda t=p_text: self._set_prompt(t)
            )
            btn_p.grid(row=0, column=idx, padx=(0, 6))
        
        # Chat History
        self.chat_box = ctk.CTkTextbox(self, fg_color=GlassTheme.CARD_BG, text_color=GlassTheme.TEXT_SECONDARY, font=ctk.CTkFont(size=12))
        self.chat_box.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")
        self.chat_box.tag_config("User", foreground=GlassTheme.ACCENT_CYAN, justify=tk.RIGHT)
        self.chat_box.tag_config("Co-Pilot", foreground=GlassTheme.TEXT_SECONDARY, justify=tk.LEFT)
        self.chat_box.insert("end", "Co-Pilot:\n", "Co-Pilot")
        self.chat_box.insert("end", "Welcome! Make sure your target page is open in the active browser. What would you like me to automate?\n\n(e.g., 'Click login, type {{Username}} into email field, and submit')\n\n", "Co-Pilot")
        self.chat_box.configure(state="disabled")
        
        # Loading Indicator Bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self, height=4, progress_color=GlassTheme.ACCENT_CYAN)
        self.progress_bar.grid(row=3, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.grid_remove()
        
        # Input Area
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_prompt = ctk.CTkTextbox(input_frame, height=70, fg_color=GlassTheme.CARD_BG_SECONDARY, text_color=GlassTheme.TEXT_PRIMARY)
        self.entry_prompt.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry_prompt.bind("<Return>", self._handle_return_key)
        
        self.btn_send = GlassButton(input_frame, text="Send 🚀", width=80, height=70, accent_color=GlassTheme.ACCENT_BLUE, command=self._handle_send)
        self.btn_send.grid(row=0, column=1)
        
        # Verification Controls Frame (Hidden initially)
        self.verify_frame = ctk.CTkFrame(self, fg_color=GlassTheme.CARD_BG_SECONDARY)
        self.verify_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.verify_frame.grid_columnconfigure(0, weight=1)
        self.verify_frame.grid_remove()
        
        # Step header & counter
        v_head_frame = ctk.CTkFrame(self.verify_frame, fg_color="transparent")
        v_head_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(6, 2))
        v_head_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_verify_step = ctk.CTkLabel(v_head_frame, text="Step 1 of 3", font=ctk.CTkFont(size=12, weight="bold"), text_color=GlassTheme.ACCENT_CYAN)
        self.lbl_verify_step.grid(row=0, column=0, sticky="w")
        
        self.lbl_verify = ctk.CTkLabel(v_head_frame, text="Is the highlighted element correct?", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_verify.grid(row=0, column=1, sticky="e")
        
        # Editable Selector
        selector_frame = ctk.CTkFrame(self.verify_frame, fg_color="transparent")
        selector_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=4)
        selector_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_selector = ctk.CTkEntry(selector_frame, placeholder_text="CSS Selector")
        self.entry_selector.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.btn_test_selector = GlassButton(selector_frame, text="🧪 Test", width=70, accent_color=GlassTheme.ACCENT_BLUE, command=self._test_edited_selector)
        self.btn_test_selector.grid(row=0, column=1)

        # Guided Verification Navigation Buttons
        btn_frame = ctk.CTkFrame(self.verify_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=8)
        
        self.btn_prev = GlassButton(btn_frame, text="⏮️ Prev", width=70, command=self._verify_prev, fg_color=GlassTheme.CARD_BORDER)
        self.btn_prev.grid(row=0, column=0, padx=4)
        
        GlassButton(btn_frame, text="✅ Next / Approve", command=self._verify_yes, fg_color=GlassTheme.ACCENT_EMERALD, text_color="black").grid(row=0, column=1, padx=4)
        GlassButton(btn_frame, text="🗑️ Skip", command=self._verify_no, fg_color=GlassTheme.CARD_BORDER).grid(row=0, column=2, padx=4)
        
        # State
        self.generated_events: List[Tuple[MacroEvent, str]] = []
        self.current_verify_idx = 0
        
    def _set_prompt(self, text: str):
        self.entry_prompt.delete("1.0", "end")
        self.entry_prompt.insert("1.0", text)
        
    def _handle_return_key(self, event):
        if event.state & 0x0001:  # Shift key pressed
            return None
        else:
            self._handle_send()
            return "break"

    def _set_status(self, text: str, color: str):
        self.lbl_status_badge.configure(text=text, text_color=color)

    def _show_loading(self, active: bool):
        if active:
            self.progress_bar.grid()
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.grid_remove()

    def _append_chat(self, text: str, sender: str = "Co-Pilot"):
        self.chat_box.configure(state="normal")
        if sender == "You":
            self.chat_box.insert("end", f"[{sender}]\n", "User")
            self.chat_box.insert("end", f"{text}\n\n", "User")
        else:
            self.chat_box.insert("end", f"[{sender}]\n", "Co-Pilot")
            self.chat_box.insert("end", f"{text}\n\n", "Co-Pilot")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def _handle_send(self):
        prompt = self.entry_prompt.get("1.0", "end-1c").strip()
        if not prompt:
            return
            
        self.entry_prompt.delete("1.0", "end")
        self._append_chat(prompt, "You")
        
        # Connection Check via TCP Probe
        if not self.cdp.is_alive():
            self._set_status("🔍 Connecting...", GlassTheme.ACCENT_CYAN)
            self._append_chat("Searching for active browser...", "Co-Pilot")
            ws_url = self.nst.find_running_browser_ws_url()
            
            if ws_url:
                self.cdp.connect(ws_url)
                self._append_chat("✅ Connected to active Browser!", "Co-Pilot")
            else:
                email = simpledialog.askstring("NST Profile", "No active browser detected.\n\nEnter Profile Email or Name to launch via API:")
                if not email:
                    self._set_status("🔴 Not Connected", GlassTheme.CARD_BORDER)
                    self._append_chat("Training cancelled. Active profile required.", "Co-Pilot")
                    return
                
                try:
                    self._append_chat(f"Launching profile '{email}'...", "Co-Pilot")
                    ws_url = self.nst.prepare_and_launch(email, "")
                    if ws_url:
                        self.cdp.connect(ws_url)
                        self._append_chat("✅ Connected to launched Browser!", "Co-Pilot")
                    else:
                        self._set_status("🔴 Connection Failed", GlassTheme.CARD_BORDER)
                        self._append_chat("Failed to get debugger URL from NST.", "Co-Pilot")
                        return
                except Exception as e:
                    self._set_status("🔴 Connection Error", GlassTheme.CARD_BORDER)
                    self._append_chat(f"Error connecting to NST: {e}", "Co-Pilot")
                    return
                    
        self._set_status("⏳ Scanning DOM...", GlassTheme.ACCENT_CYAN)
        self._show_loading(True)
        self.btn_send.configure(state="disabled")
        
        # JS IIFE for DOM Extraction
        js_code = """
        (() => {
            const raw = Array.from(document.querySelectorAll('a, button, input, select, textarea, [role="button"], [onclick], [tabindex]'));
            const elements = [];
            const pageUrl = window.location.href;
            const pageTitle = document.title;
            
            for (let el of raw) {
                if (elements.length >= 100) break;
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;
                
                let tag = el.tagName.toLowerCase();
                let selector = tag;
                
                if (el.id) {
                    selector = tag + '#' + CSS.escape(el.id);
                } else if (el.name) {
                    selector = tag + '[name="' + el.name + '"]';
                } else if (el.getAttribute('data-testid')) {
                    selector = tag + '[data-testid="' + el.getAttribute('data-testid') + '"]';
                } else if (el.placeholder) {
                    selector = tag + '[placeholder="' + el.placeholder + '"]';
                } else if (el.getAttribute('aria-label')) {
                    selector = tag + '[aria-label="' + el.getAttribute('aria-label') + '"]';
                } else if (el.className && typeof el.className === 'string') {
                    const cleanClasses = el.className.trim().split(/\\s+/).filter(c => c && !c.includes(':') && !c.includes('/') && c.length < 30);
                    if (cleanClasses.length > 0) {
                        selector = tag + '.' + cleanClasses.slice(0, 2).map(c => CSS.escape(c)).join('.');
                    }
                }
                
                // Associated label or nearby prompt text lookup
                let labelText = '';
                if (el.id) {
                    try {
                        const lbl = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
                        if (lbl) labelText = (lbl.innerText || lbl.textContent || '').trim();
                    } catch(e) {}
                }
                if (!labelText && el.parentElement) {
                    try {
                        const pLbl = el.parentElement.querySelector('label') || el.closest('label') || (el.parentElement.previousElementSibling && el.parentElement.previousElementSibling.tagName.toLowerCase() === 'label' ? el.parentElement.previousElementSibling : null);
                        if (pLbl) labelText = (pLbl.innerText || pLbl.textContent || '').trim();
                    } catch(e) {}
                }
                
                elements.push({
                    id: elements.length,
                    tag: tag,
                    text: (el.innerText || el.value || '').trim().substring(0, 60),
                    label: labelText.substring(0, 80),
                    type: el.type || '',
                    name: el.name || '',
                    placeholder: el.placeholder || '',
                    aria: el.getAttribute('aria-label') || '',
                    selector: selector
                });
            }
            return {
                url: pageUrl,
                title: pageTitle,
                elements: elements
            };
        })()
        """
        
        def bg_task():
            try:
                dom_data = self.cdp.evaluate_js_all_frames(js_code)
                self.after(0, lambda: self._set_status("🤖 AI Thinking...", GlassTheme.ACCENT_PURPLE))
                self.after(0, lambda: self._append_chat("DOM scanned across all page frames & iframes. Asking AI Co-Pilot to map step-by-step actions...", "Co-Pilot"))
                
                self._process_prompt_ai(prompt, dom_data or {})
            except Exception as e:
                msg = f"Error scanning page DOM: {str(e)}"
                self.after(0, lambda m=msg: self._append_chat(m, "Co-Pilot"))
                self.after(0, lambda: self._set_status("🔴 Error", GlassTheme.CARD_BORDER))
                self.after(0, lambda: self._show_loading(False))
                self.after(0, lambda: self.btn_send.configure(state="normal"))
                
        threading.Thread(target=bg_task, daemon=True).start()
        
    def _process_prompt_ai(self, user_prompt: str, dom_info: dict):
        try:
            elements = dom_info.get("elements", [])
            title = dom_info.get("title", "")
            url = dom_info.get("url", "")
            
            ai_prompt = f"""You are an expert Automation Macro Builder.
The user wants to perform this web automation task: "{user_prompt}"

Page Context:
- Title: {title}
- URL: {url}

Visible interactable elements on page ({len(elements)} items):
{json.dumps(elements, indent=2)}

Map the user's intent into a clear sequence of step-by-step macro actions.
You MUST generate a step for EVERY action requested by the user (inputs, dropdowns, checkboxes, buttons).

CRITICAL SELECTOR RULES:
1. Prefer using the exact 'selector' field from the element list above matching the field label/text.
2. If an element isn't in the list, synthesize a concise CSS selector based on HTML attributes (e.g. "input[name='first_name']", "select[name='ethnicity']", "input[value='Day 1']").
3. NEVER return an empty array if the user specified actions to automate.

Supported actions:
- "click": click element (selector required)
- "type": type text into input (selector required, text required; use {{{{VarName}}}} for templates)
- "select": select option in dropdown (selector required, text required)
- "wait": pause execution (delay_ms required, e.g. 1000)
- "navigate": open URL (url required)

CRITICAL JSON FORMATTING:
1. Return ONLY valid JSON array of step objects.
2. Inside selector strings, use SINGLE QUOTES for HTML attributes (e.g. "input[name='mobile']", NEVER double quotes inside double quotes).

Example output:
[
  {{
    "action": "type",
    "selector": "input#textbox-12",
    "text": "{{{{First_Name}}}}",
    "description": "Type first name into First Name input"
  }}
]
"""
            response = self.ai.chat_text(ai_prompt)
            
            try:
                steps = self._parse_and_repair_json(response)
                self.after(0, lambda: self._prepare_verification(steps))
            except Exception as parse_err:
                self.after(0, lambda: self._append_chat(f"AI response format error. Raw output:\n{response}", "Co-Pilot"))
                self.after(0, lambda: self._set_status("🔴 Parse Error", GlassTheme.CARD_BORDER))
                self.after(0, lambda: self._show_loading(False))
                self.after(0, lambda: self.btn_send.configure(state="normal"))
        except Exception as e:
            msg = f"AI Generation error: {str(e)}"
            self.after(0, lambda m=msg: self._append_chat(m, "Co-Pilot"))
            self.after(0, lambda: self._set_status("🔴 Error", GlassTheme.CARD_BORDER))
            self.after(0, lambda: self._show_loading(False))
            self.after(0, lambda: self.btn_send.configure(state="normal"))

    def _parse_and_repair_json(self, raw_text: str) -> list:
        import re
        # Step 0: Strip markdown fences if present (```json ... ```)
        fence_match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_text, re.DOTALL)
        if fence_match:
            clean_text = fence_match.group(1).strip()
        else:
            start_idx = raw_text.find('[')
            end_idx = raw_text.rfind(']')
            if start_idx != -1 and end_idx != -1:
                clean_text = raw_text[start_idx:end_idx+1].strip()
            else:
                clean_text = raw_text.strip("` \n\r\t")

        try:
            res = json.loads(clean_text)
            if isinstance(res, list):
                return res
        except json.JSONDecodeError:
            pass

        # Step 1: Replace unescaped double quotes inside CSS attribute selector brackets like [name="mobile"] -> [name='mobile']
        def _fix_attr_brackets(m):
            prefix = m.group(1)
            val = m.group(2)
            val_fixed = re.sub(r'\[([a-zA-Z0-9_-]+)="([^"]+)"\]', r"[\1='\2']", val)
            return f'{prefix}{val_fixed}"'

        repaired = re.sub(r'("selector"\s*:\s*")([^"\r\n]*?\[[^\]\r\n]+\][^"\r\n]*?)"', _fix_attr_brackets, clean_text)
        
        # Step 2: Replace any remaining unescaped quotes in selector lines
        lines = []
        for line in repaired.splitlines():
            if '"selector":' in line:
                m = re.match(r'(\s*"selector"\s*:\s*")(.*)("\s*,?\s*)$', line)
                if m:
                    inner = m.group(2)
                    inner_clean = inner.replace('"', "'")
                    line = f'{m.group(1)}{inner_clean}{m.group(3)}'
            lines.append(line)
        repaired_final = "\n".join(lines)
        
        try:
            res = json.loads(repaired_final)
            if isinstance(res, list):
                return res
        except Exception:
            pass

        # Fallback regex object parser
        steps = []
        matches = re.finditer(r'\{\s*"action"\s*:.*?\}(?=\s*\,|\s*\]|\s*\n)', clean_text + "]", re.DOTALL)
        for m in matches:
            obj_str = m.group(0)
            act = re.search(r'"action"\s*:\s*"([^"]+)"', obj_str)
            sel = re.search(r'"selector"\s*:\s*"(.*?)"\s*,\s*', obj_str)
            txt = re.search(r'"text"\s*:\s*"(.*?)"\s*,\s*', obj_str)
            desc = re.search(r'"description"\s*:\s*"(.*?)"\s*\}', obj_str)
            if act:
                sel_val = sel.group(1) if sel else ""
                sel_val = sel_val.replace('"', "'")
                steps.append({
                    "action": act.group(1),
                    "selector": sel_val,
                    "text": txt.group(1) if txt else "",
                    "description": desc.group(1) if desc else ""
                })
        if steps:
            return steps
        raise ValueError("Could not parse AI response as JSON step array.")

    def _prepare_verification(self, steps: list):
        self._show_loading(False)
        if not steps:
            self._append_chat("No valid steps generated. Try rephrasing your prompt.", "Co-Pilot")
            self._set_status("🟢 Ready", GlassTheme.ACCENT_EMERALD)
            self.btn_send.configure(state="normal")
            return
            
        self._set_status("✨ Verification", GlassTheme.ACCENT_CYAN)
        self._append_chat(f"Generated {len(steps)} steps! Entering Guided Verification mode...", "Co-Pilot")
        self.generated_events = []
        
        for step in steps:
            action = step.get("action", "click").lower()
            selector = step.get("selector", "")
            desc = step.get("description", f"{action.capitalize()} {selector}")
            text_val = step.get("text", "")
            delay_ms = step.get("delay_ms", 1000)
            
            if action in ("click", "type", "select"):
                ev = MacroEvent(event_type=EventType.CDP_PHYSICAL_INPUT)
                ev.selector = selector
                if action in ("type", "select"):
                    ev.text = text_val
                ev.delay_after_ms = 800.0
                ev.error_policy = ErrorPolicy.RETRY_3
                ev.comment = desc
                self.generated_events.append((ev, desc))
            elif action == "wait":
                ev = MacroEvent(event_type=EventType.DELAY)
                ev.delay_ms = float(delay_ms)
                ev.comment = desc
                self.generated_events.append((ev, desc))
            elif action == "navigate":
                ev = MacroEvent(event_type=EventType.NST_PREPARE_PROFILE)
                ev.text = step.get("url", "")
                ev.comment = desc
                self.generated_events.append((ev, desc))
            else:
                ev = MacroEvent(event_type=EventType.CDP_PHYSICAL_INPUT)
                ev.selector = selector
                ev.comment = desc
                self.generated_events.append((ev, desc))
            
        self.current_verify_idx = 0
        self.verify_frame.grid()
        self._highlight_current_step()
        
    def _test_edited_selector(self, selector_override=None):
        selector = selector_override if isinstance(selector_override, str) else self.entry_selector.get().strip()
        if not selector: return
        
        safe_selector = json.dumps(selector)
        js_highlight = f"""
        (() => {{
            document.querySelectorAll('.shohoj-ai-highlight').forEach(el => {{
                el.style.outline = el.dataset.oldOutline || '';
                el.classList.remove('shohoj-ai-highlight');
            }});
            try {{
                const el = document.querySelector({safe_selector});
                if (el) {{
                    el.dataset.oldOutline = el.style.outline;
                    el.style.outline = '4px solid #30D158';
                    el.classList.add('shohoj-ai-highlight');
                    el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    return true;
                }}
            }} catch(e) {{}}
            return false;
        }})()
        """
        def bg_highlight():
            try:
                found = self.cdp.evaluate_js_all_frames(js_highlight)
                if not found:
                    self.after(0, lambda: self._append_chat(f"⚠️ Warning: Could not locate selector '{selector}' on page or inside iframe!", "Co-Pilot"))
            except Exception:
                pass
        threading.Thread(target=bg_highlight, daemon=True).start()

    def _highlight_current_step(self):
        total = len(self.generated_events)
        if total == 0 or self.current_verify_idx >= total:
            self._finish_verification()
            return
            
        self.lbl_verify_step.configure(text=f"Step {self.current_verify_idx + 1} of {total}")
        self.btn_prev.configure(state="normal" if self.current_verify_idx > 0 else "disabled")
        
        ev, desc = self.generated_events[self.current_verify_idx]
        target_info = f"Target: {ev.selector}" if ev.selector else (f"Text/URL: {ev.text}" if ev.text else "")
        self._append_chat(f"Step {self.current_verify_idx + 1}/{total}: {desc}\n{target_info}", "Co-Pilot")
        
        self.entry_selector.delete(0, "end")
        if ev.selector:
            self.entry_selector.insert(0, ev.selector)
            self._test_edited_selector(ev.selector)
            
    def _verify_yes(self):
        if self.current_verify_idx < len(self.generated_events):
            ev, desc = self.generated_events[self.current_verify_idx]
            if ev.selector:
                ev.selector = self.entry_selector.get().strip()
            
        self.current_verify_idx += 1
        self._highlight_current_step()
        
    def _verify_prev(self):
        if self.current_verify_idx > 0:
            self.current_verify_idx -= 1
            self._highlight_current_step()

    def _verify_no(self):
        if self.current_verify_idx < len(self.generated_events):
            self._append_chat(f"Dropped Step {self.current_verify_idx + 1}.", "Co-Pilot")
            self.generated_events.pop(self.current_verify_idx)
            self._highlight_current_step()
        
    def _clear_highlights_bg(self):
        def bg_clean():
            try:
                self.cdp.evaluate_js_all_frames("""(() => {
                    document.querySelectorAll('.shohoj-ai-highlight').forEach(el => {
                        el.style.outline = el.dataset.oldOutline || '';
                        el.classList.remove('shohoj-ai-highlight');
                    });
                })()""")
            except Exception: pass
        threading.Thread(target=bg_clean, daemon=True).start()

    def _finish_verification(self):
        self.verify_frame.grid_remove()
        self._clear_highlights_bg()
        
        final_events = [ev for ev, desc in self.generated_events]
        self._set_status("🟢 Completed", GlassTheme.ACCENT_EMERALD)
        self._append_chat(f"🎉 Guided Verification complete! Pushing {len(final_events)} steps to Timeline.", "Co-Pilot")
        self.btn_send.configure(state="normal")
        
        if self.on_complete:
            self.after(800, lambda: self.on_complete(final_events))
            self.after(1400, self.destroy)

    def _on_close(self):
        self._clear_highlights_bg()
        self.destroy()
