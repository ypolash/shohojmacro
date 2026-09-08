import customtkinter as ctk
import threading
import httpx
from typing import Callable
from shohoj_macro.gui.glass_theme import GlassTheme, GlassButton
from shohoj_macro.core.settings_manager import SettingsManager

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, current_settings: dict, on_save: Callable[[dict], None]):
        super().__init__(master)
        
        self.old_settings = dict(current_settings)
        self.on_save = on_save
        self.settings_mgr = SettingsManager()
        
        self.title("⚙️ Operation Settings")
        self.geometry("600x600")
        self.configure(fg_color=GlassTheme.BG_DARK)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()
        
        # Center window
        if master:
            self.update_idletasks()
            x = master.winfo_x() + (master.winfo_width() // 2) - (600 // 2)
            y = master.winfo_y() + (master.winfo_height() // 2) - (600 // 2)
            self.geometry(f"+{x}+{y}")
            
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.tabview = ctk.CTkTabview(self, width=550, height=500, fg_color=GlassTheme.CARD_BG)
        self.tabview.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        
        self.tab_ai = self.tabview.add("🤖 AI & Vision")
        self.tab_captcha = self.tabview.add("🛡️ CAPTCHA")
        self.tab_nst = self.tabview.add("🌐 Proxy & Browser")
        self.tab_hotkeys = self.tabview.add("⌨️ Hotkeys & Stealth")
        
        self._build_ai_tab()
        self._build_captcha_tab()
        self._build_nst_tab()
        self._build_hotkeys_tab()
        
        # Bottom Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.btn_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_status = ctk.CTkLabel(self.btn_frame, text="", text_color=GlassTheme.ACCENT_CYAN)
        self.lbl_status.grid(row=0, column=0, sticky="w")
        
        ctk.CTkButton(self.btn_frame, text="Cancel", width=80, fg_color=GlassTheme.CARD_BG_SECONDARY, hover_color="#333A4D", command=self.destroy).grid(row=0, column=1, padx=(0, 10))
        GlassButton(self.btn_frame, text="Save Settings", width=120, accent_color=GlassTheme.ACCENT_BLUE, command=self._save_settings).grid(row=0, column=2)

    def _build_ai_tab(self):
        ctk.CTkLabel(self.tab_ai, text="OpenRouter API Key:", text_color=GlassTheme.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(10, 2))
        
        api_frame = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        api_frame.pack(anchor="w", fill="x", padx=10, pady=(0, 15))
        
        self.entry_api_key = ctk.CTkEntry(api_frame, show="*", width=240)
        self.entry_api_key.pack(side="left", fill="x", expand=True)
        self.entry_api_key.insert(0, self.settings_mgr.get("ai", "openrouter_api_key", ""))
        
        self.btn_test_ai = ctk.CTkButton(api_frame, text="Test", width=60, command=self._test_ai_connection)
        self.btn_test_ai.pack(side="right", padx=(5, 0))
        
        lbl_model_frame = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        lbl_model_frame.pack(fill="x", padx=10, pady=(5, 2))
        ctk.CTkLabel(lbl_model_frame, text="Vision AI Model:", text_color=GlassTheme.TEXT_PRIMARY).pack(side="left")
        
        self.btn_fetch_models = ctk.CTkButton(
            lbl_model_frame, text="Fetch Live Models", width=100, height=20, 
            font=ctk.CTkFont(size=10), command=self._fetch_models_async
        )
        self.btn_fetch_models.pack(side="right")

        model_frame = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        model_frame.pack(anchor="w", fill="x", padx=10, pady=(0, 10))
        
        default_model = self.settings_mgr.get("ai", "model", "google/gemini-flash-1.5")
        self.cmb_model = ctk.CTkComboBox(model_frame, values=[default_model, "meta-llama/llama-3.2-90b-vision-instruct"], dropdown_font=ctk.CTkFont(size=12))
        self.cmb_model.pack(side="left", fill="x", expand=True)
        self.cmb_model.set(default_model)
        
        self.btn_test_model = ctk.CTkButton(model_frame, text="Test Model", width=80, command=self._test_model_connection)
        self.btn_test_model.pack(side="right", padx=(5, 0))

    def _test_ai_connection(self):
        self.btn_test_ai.configure(text="...", state="disabled")
        threading.Thread(target=self._test_ai_worker, daemon=True).start()
        
    def _test_ai_worker(self):
        try:
            headers = {"Authorization": f"Bearer {self.entry_api_key.get()}"}
            resp = httpx.get("https://openrouter.ai/api/v1/auth/key", headers=headers, timeout=10.0)
            if resp.status_code == 200:
                self.after(0, lambda: self.btn_test_ai.configure(text="OK", fg_color="#143A22", text_color=GlassTheme.ACCENT_EMERALD))
            else:
                self.after(0, lambda: self.btn_test_ai.configure(text="FAIL", fg_color="#3A181C", text_color=GlassTheme.ACCENT_RED))
        except Exception:
            self.after(0, lambda: self.btn_test_ai.configure(text="ERR", fg_color="#3A181C", text_color=GlassTheme.ACCENT_RED))
        
        # Reset button styling after 3 seconds
        default_fg = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        default_text = ctk.ThemeManager.theme["CTkButton"]["text_color"]
        self.after(3000, lambda: self.btn_test_ai.configure(text="Test", fg_color=default_fg, text_color=default_text, state="normal"))

    def _test_model_connection(self):
        self.btn_test_model.configure(text="...", state="disabled")
        threading.Thread(target=self._test_model_worker, daemon=True).start()
        
    def _test_model_worker(self):
        try:
            headers = {
                "Authorization": f"Bearer {self.entry_api_key.get()}", 
                "Content-Type": "application/json",
                "HTTP-Referer": "https://shohojmacro.com",
                "X-Title": "Shohoj Macro"
            }
            payload = {
                "model": self.cmb_model.get(),
                "messages": [{"role": "user", "content": "hi"}]
            }
            resp = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15.0)
            if resp.status_code == 200:
                self.after(0, lambda: self.btn_test_model.configure(text="OK", fg_color="#143A22", text_color=GlassTheme.ACCENT_EMERALD))
            else:
                print(f"[Model Test Failed] HTTP {resp.status_code}: {resp.text}")
                self.after(0, lambda: self.btn_test_model.configure(text="FAIL", fg_color="#3A181C", text_color=GlassTheme.ACCENT_RED))
        except Exception:
            self.after(0, lambda: self.btn_test_model.configure(text="ERR", fg_color="#3A181C", text_color=GlassTheme.ACCENT_RED))
            
        default_fg = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        default_text = ctk.ThemeManager.theme["CTkButton"]["text_color"]
        self.after(3000, lambda: self.btn_test_model.configure(text="Test Model", fg_color=default_fg, text_color=default_text, state="normal"))

    def _fetch_models_async(self):
        self.btn_fetch_models.configure(text="Fetching...", state="disabled")
        threading.Thread(target=self._fetch_models_worker, daemon=True).start()
        
    def _fetch_models_worker(self):
        try:
            resp = httpx.get("https://openrouter.ai/api/v1/models", timeout=10.0)
            if resp.status_code == 200:
                models = resp.json().get("data", [])
                model_ids = [m["id"] for m in models if "vision" in m.get("architecture", {}).get("modality", "") or "vision" in m["id"] or "gemini" in m["id"]]
                if not model_ids:
                    model_ids = [m["id"] for m in models]
                model_ids.sort()
                self.after(0, lambda: self.cmb_model.configure(values=model_ids))
                self.after(0, lambda: self.btn_fetch_models.configure(text="Fetched!", text_color="green"))
            else:
                self.after(0, lambda: self.btn_fetch_models.configure(text="Error fetching"))
        except Exception as e:
            self.after(0, lambda: self.btn_fetch_models.configure(text="Network Error"))
        
        self.after(2000, lambda: self.btn_fetch_models.configure(text="Fetch Live Models", state="normal", text_color=["gray10", "gray90"]))

    def _build_captcha_tab(self):
        ctk.CTkLabel(self.tab_captcha, text="Max AI Solver Retry Rounds:", text_color=GlassTheme.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(10, 2))
        self.entry_rounds = ctk.CTkEntry(self.tab_captcha)
        self.entry_rounds.pack(anchor="w", fill="x", padx=10, pady=(0, 15))
        self.entry_rounds.insert(0, str(self.settings_mgr.get("captcha", "max_retry_rounds", 4)))
        
        ctk.CTkLabel(self.tab_captcha, text="ReCAPTCHA Vision Prompt:", text_color=GlassTheme.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(10, 2))
        ctk.CTkLabel(self.tab_captcha, text="(Use {instruction} as the placeholder for the challenge text)", font=ctk.CTkFont(size=10, slant="italic"), text_color=GlassTheme.TEXT_SECONDARY).pack(anchor="w", padx=10, pady=0)
        
        self.txt_prompt = ctk.CTkTextbox(self.tab_captcha, height=200)
        self.txt_prompt.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self.txt_prompt.insert("0.0", self.settings_mgr.get("captcha", "custom_prompt", ""))

    def _build_nst_tab(self):
        ctk.CTkLabel(self.tab_nst, text="NST Browser API Key:", text_color=GlassTheme.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(10, 2))
        self.entry_nst_key = ctk.CTkEntry(self.tab_nst, show="*", width=300)
        self.entry_nst_key.pack(anchor="w", fill="x", padx=10, pady=(0, 15))
        self.entry_nst_key.insert(0, self.settings_mgr.get("nst", "api_key", ""))
        
        ctk.CTkLabel(self.tab_nst, text="NST Local Endpoint URL:", text_color=GlassTheme.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(10, 2))
        self.entry_nst_url = ctk.CTkEntry(self.tab_nst, width=300)
        self.entry_nst_url.pack(anchor="w", fill="x", padx=10, pady=(0, 20))
        self.entry_nst_url.insert(0, self.settings_mgr.get("nst", "local_url", "http://localhost:8848"))
        
        fallback_val = self.settings_mgr.get("nst", "enable_gui_fallback", True)
        self.chk_fallback = ctk.CTkSwitch(self.tab_nst, text="Enable GUI Visual Fallback (if NST fails)")
        self.chk_fallback.pack(anchor="w", padx=10)
        if fallback_val:
            self.chk_fallback.select()
        else:
            self.chk_fallback.deselect()

    def _build_hotkeys_tab(self):
        ctk.CTkLabel(self.tab_hotkeys, text="Global Hotkeys", font=ctk.CTkFont(size=12, weight="bold"), text_color=GlassTheme.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(10, 5))
        
        f_hk1 = ctk.CTkFrame(self.tab_hotkeys, fg_color="transparent")
        f_hk1.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(f_hk1, text="Record / Stop Hotkey:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_rec_key = ctk.CTkEntry(f_hk1, width=100)
        self.ent_rec_key.insert(0, self.old_settings.get("record_hotkey", "<f8>"))
        self.ent_rec_key.pack(side="right")

        f_hk2 = ctk.CTkFrame(self.tab_hotkeys, fg_color="transparent")
        f_hk2.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(f_hk2, text="Play / Pause Hotkey:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_play_key = ctk.CTkEntry(f_hk2, width=100)
        self.ent_play_key.insert(0, self.old_settings.get("play_hotkey", "<f9>"))
        self.ent_play_key.pack(side="right")

        f_hk3 = ctk.CTkFrame(self.tab_hotkeys, fg_color="transparent")
        f_hk3.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(f_hk3, text="Emergency Kill Switch:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_stop_key = ctk.CTkEntry(f_hk3, width=100)
        self.ent_stop_key.insert(0, self.old_settings.get("stop_hotkey", "<f10>"))
        self.ent_stop_key.pack(side="right")
        
        ctk.CTkLabel(self.tab_hotkeys, text="StealthCore & Humanizer Physics", font=ctk.CTkFont(size=12, weight="bold"), text_color=GlassTheme.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(20, 5))
        
        self.chk_humanizer = ctk.CTkCheckBox(self.tab_hotkeys, text="Enable WindMouse & Natural Bézier Curves")
        if self.old_settings.get("humanizer_enabled", True):
            self.chk_humanizer.select()
        self.chk_humanizer.pack(anchor="w", padx=10, pady=4)

        self.chk_biorhythm = ctk.CTkCheckBox(self.tab_hotkeys, text="Enable Bio-Rhythm Fatigue")
        if self.old_settings.get("bio_rhythm_enabled", True):
            self.chk_biorhythm.select()
        self.chk_biorhythm.pack(anchor="w", padx=10, pady=4)

        self.chk_block_input = ctk.CTkCheckBox(self.tab_hotkeys, text="Shield Physical Input during Playback")
        if self.old_settings.get("block_physical_input", False):
            self.chk_block_input.select()
        self.chk_block_input.pack(anchor="w", padx=10, pady=4)
        
        # Humanizer speed
        ctk.CTkLabel(self.tab_hotkeys, text="Humanizer Speed Multiplier:", anchor="w").pack(fill="x", padx=10, pady=(15, 2))
        speed_frame = ctk.CTkFrame(self.tab_hotkeys, fg_color="transparent")
        speed_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        current_speed = self.settings_mgr.get("ai", "humanizer_speed_multiplier", 1.0)
        self.lbl_speed_val = ctk.CTkLabel(speed_frame, text=f"{current_speed}x", width=40)
        self.lbl_speed_val.pack(side="right")
        self.slider_speed = ctk.CTkSlider(speed_frame, from_=0.1, to=3.0, number_of_steps=29, command=lambda v: self.lbl_speed_val.configure(text=f"{v:.1f}x"))
        self.slider_speed.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.slider_speed.set(current_speed)


    def _save_settings(self):
        try:
            rounds = int(self.entry_rounds.get())
        except ValueError:
            rounds = 4

        # Save to the JSON persist manager
        self.settings_mgr.update_category("ai", {
            "openrouter_api_key": self.entry_api_key.get(),
            "model": self.cmb_model.get(),
            "humanizer_speed_multiplier": round(self.slider_speed.get(), 1)
        })
        
        self.settings_mgr.update_category("captcha", {
            "max_retry_rounds": rounds,
            "custom_prompt": self.txt_prompt.get("0.0", "end").strip()
        })
        
        self.settings_mgr.update_category("nst", {
            "api_key": self.entry_nst_key.get(),
            "local_url": self.entry_nst_url.get(),
            "enable_gui_fallback": bool(self.chk_fallback.get())
        })
        self.settings_mgr.save()
        
        # Also invoke the legacy save callback for hotkeys
        self.old_settings["record_hotkey"] = self.ent_rec_key.get()
        self.old_settings["play_hotkey"] = self.ent_play_key.get()
        self.old_settings["stop_hotkey"] = self.ent_stop_key.get()
        self.old_settings["humanizer_enabled"] = bool(self.chk_humanizer.get())
        self.old_settings["bio_rhythm_enabled"] = bool(self.chk_biorhythm.get())
        self.old_settings["block_physical_input"] = bool(self.chk_block_input.get())

        if self.on_save:
            self.on_save(self.old_settings)

        self.lbl_status.configure(text="Settings Saved!")
        self.after(1000, self.destroy)
