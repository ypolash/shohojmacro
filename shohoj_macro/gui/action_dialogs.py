"""
Action Property Editors & Modals
Dedicated dialogs to edit Mouse, Keyboard, Delay, Humanizer Zones, and Pixel Triggers.
"""

import customtkinter as ctk
from typing import Callable, Optional
from shohoj_macro.core.events import MacroEvent, EventType, ErrorPolicy
from shohoj_macro.gui.glass_theme import GlassTheme, GlassButton
from shohoj_macro.gui.screen_overlay import ScreenOverlaySniper


class BaseActionDialog(ctk.CTkToplevel):
    def __init__(self, master, event: MacroEvent, on_save: Callable[[MacroEvent], None], title: str = "Edit Action"):
        super().__init__(master)
        self.event = event
        self.on_save = on_save

        self.title(title)
        self.geometry("420x480")
        self.configure(fg_color=GlassTheme.BG_DARK)
        self.attributes("-topmost", True)
        self.grab_set()

        # Content frame
        self.body = ctk.CTkFrame(self, fg_color=GlassTheme.CARD_BG, corner_radius=14)
        self.body.pack(fill="both", expand=True, padx=16, pady=16)

        # Title
        self.lbl_title = ctk.CTkLabel(
            self.body,
            text=title,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=15, weight="bold"),
            text_color=GlassTheme.ACCENT_CYAN,
        )
        self.lbl_title.pack(pady=(14, 10))

    def _add_delay_and_policy_fields(self):
        # Delay after
        f_delay = ctk.CTkFrame(self.body, fg_color="transparent")
        f_delay.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(f_delay, text="Delay After (ms):", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_delay_after = ctk.CTkEntry(f_delay, width=90)
        self.ent_delay_after.insert(0, str(int(self.event.delay_after_ms)))
        self.ent_delay_after.pack(side="right")

        # Error Policy
        f_err = ctk.CTkFrame(self.body, fg_color="transparent")
        f_err.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(f_err, text="Error Policy:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.opt_error_policy = ctk.CTkOptionMenu(
            f_err,
            values=["STOP", "SKIP", "RETRY_3"],
            width=110,
        )
        self.opt_error_policy.set(self.event.error_policy.value)
        self.opt_error_policy.pack(side="right")

    def _add_bottom_buttons(self, on_save_callback: Callable):
        btn_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=16, pady=14)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            width=80,
            command=self.destroy,
        ).pack(side="left")

        GlassButton(
            btn_frame,
            text="Save Changes",
            accent_color=GlassTheme.ACCENT_BLUE,
            width=120,
            command=on_save_callback,
        ).pack(side="right")


class MouseActionDialog(BaseActionDialog):
    """Dialog for editing Mouse Click / Move events."""

    def __init__(self, master, event: MacroEvent, on_save: Callable[[MacroEvent], None]):
        super().__init__(master, event, on_save, title="🖱️ Edit Mouse Action")

        # Coordinates with Sniper Picker button
        f_coords = ctk.CTkFrame(self.body, fg_color="transparent")
        f_coords.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(f_coords, text="Coordinates:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")

        self.ent_x = ctk.CTkEntry(f_coords, width=60)
        self.ent_x.insert(0, str(self.event.x))
        self.ent_x.pack(side="left", padx=4)

        self.ent_y = ctk.CTkEntry(f_coords, width=60)
        self.ent_y.insert(0, str(self.event.y))
        self.ent_y.pack(side="left", padx=4)

        ctk.CTkButton(
            f_coords,
            text="🎯 Sniper",
            width=65,
            height=28,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color=GlassTheme.ACCENT_CYAN,
            command=self._pick_coordinates,
        ).pack(side="right")

        # Button & Click Type
        f_btn = ctk.CTkFrame(self.body, fg_color="transparent")
        f_btn.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(f_btn, text="Mouse Button:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.opt_button = ctk.CTkOptionMenu(f_btn, values=["left", "right", "middle"], width=100)
        self.opt_button.set(self.event.button)
        self.opt_button.pack(side="right")

        # Human Target Radius
        f_rad = ctk.CTkFrame(self.body, fg_color="transparent")
        f_rad.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(f_rad, text="Random Target Radius (px):", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_radius = ctk.CTkEntry(f_rad, width=70)
        self.ent_radius.insert(0, str(self.event.human_target_radius))
        self.ent_radius.pack(side="right")

        # Trajectory Curve Type
        f_curve = ctk.CTkFrame(self.body, fg_color="transparent")
        f_curve.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(f_curve, text="Movement Curve:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.opt_curve = ctk.CTkOptionMenu(f_curve, values=["windmouse", "bezier", "linear", "instant"], width=110)
        self.opt_curve.set(self.event.curve_type)
        self.opt_curve.pack(side="right")

        self._add_delay_and_policy_fields()
        self._add_bottom_buttons(self._save)

    def _pick_coordinates(self):
        def on_picked(res):
            self.ent_x.delete(0, "end")
            self.ent_x.insert(0, str(res["x"]))
            self.ent_y.delete(0, "end")
            self.ent_y.insert(0, str(res["y"]))
            if res.get("radius", 0) > 0:
                self.ent_radius.delete(0, "end")
                self.ent_radius.insert(0, str(res["radius"]))

        ScreenOverlaySniper(self, mode="circle", on_selection_complete=on_picked)

    def _save(self):
        try:
            self.event.x = int(self.ent_x.get())
            self.event.y = int(self.ent_y.get())
            self.event.button = self.opt_button.get()
            self.event.human_target_radius = int(self.ent_radius.get())
            self.event.curve_type = self.opt_curve.get()
            self.event.delay_after_ms = float(self.ent_delay_after.get())
            self.event.error_policy = ErrorPolicy(self.opt_error_policy.get())
            self.on_save(self.event)
            self.destroy()
        except Exception as e:
            print(f"Validation error: {e}")


class DelayActionDialog(BaseActionDialog):
    """Dialog for editing Delay / Wait events."""

    def __init__(self, master, event: MacroEvent, on_save: Callable[[MacroEvent], None]):
        super().__init__(master, event, on_save, title="⏳ Edit Wait / Delay Action")

        f_dur = ctk.CTkFrame(self.body, fg_color="transparent")
        f_dur.pack(fill="x", padx=16, pady=10)
        ctk.CTkLabel(f_dur, text="Base Duration (ms):", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_duration = ctk.CTkEntry(f_dur, width=100)
        self.ent_duration.insert(0, str(int(self.event.delay_ms)))
        self.ent_duration.pack(side="right")

        f_jit = ctk.CTkFrame(self.body, fg_color="transparent")
        f_jit.pack(fill="x", padx=16, pady=10)
        ctk.CTkLabel(f_jit, text="Random Jitter (± ms):", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_jitter = ctk.CTkEntry(f_jit, width=100)
        self.ent_jitter.insert(0, str(int(self.event.jitter_ms)))
        self.ent_jitter.pack(side="right")

        self._add_delay_and_policy_fields()
        self._add_bottom_buttons(self._save)

    def _save(self):
        try:
            self.event.delay_ms = float(self.ent_duration.get())
            self.event.jitter_ms = float(self.ent_jitter.get())
            self.event.delay_after_ms = float(self.ent_delay_after.get())
            self.on_save(self.event)
            self.destroy()
        except Exception as e:
            print(f"Validation error: {e}")


class TextTypeActionDialog(BaseActionDialog):
    """Dialog for editing Text Typing events with optional CSV variable mapping."""

    def __init__(self, master, event: MacroEvent, on_save: Callable[[MacroEvent], None], csv_engine=None):
        super().__init__(master, event, on_save, title="⌨️ Edit Text Typing Action")
        self.csv_engine = csv_engine

        ctk.CTkLabel(self.body, text="Text String to Type (supports {{variable}} tags):", text_color=GlassTheme.TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(4, 2))
        self.txt_content = ctk.CTkTextbox(self.body, height=80)
        self.txt_content.insert("1.0", self.event.text)
        self.txt_content.pack(fill="x", padx=16, pady=(0, 8))

        # Optional CSV variable helper dropdown
        if self.csv_engine and self.csv_engine.is_loaded:
            headers = self.csv_engine.get_headers() if hasattr(self.csv_engine, 'get_headers') else getattr(self.csv_engine, 'headers', [])
            if headers:
                f_csv = ctk.CTkFrame(self.body, fg_color="transparent")
                f_csv.pack(fill="x", padx=16, pady=(0, 8))
                ctk.CTkLabel(f_csv, text="Insert CSV Column:", text_color=GlassTheme.ACCENT_CYAN, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")

                def _insert_header(choice):
                    if choice and choice != "-- Select Column --":
                        self.txt_content.insert("insert", f"{{{{{choice}}}}}")
                        self.opt_headers.set("-- Select Column --")

                self.opt_headers = ctk.CTkOptionMenu(
                    f_csv,
                    values=["-- Select Column --"] + list(headers),
                    command=_insert_header,
                    width=170,
                    height=26,
                    font=ctk.CTkFont(size=11),
                )
                self.opt_headers.set("-- Select Column --")
                self.opt_headers.pack(side="right")

        f_wpm = ctk.CTkFrame(self.body, fg_color="transparent")
        f_wpm.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(f_wpm, text="Typing Speed (WPM):", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_wpm = ctk.CTkEntry(f_wpm, width=70)
        self.ent_wpm.insert(0, str(self.event.wpm))
        self.ent_wpm.pack(side="right")

        self._add_delay_and_policy_fields()
        self._add_bottom_buttons(self._save)

    def _save(self):
        try:
            self.event.text = self.txt_content.get("1.0", "end-1c")
            self.event.wpm = int(self.ent_wpm.get())
            self.event.delay_after_ms = float(self.ent_delay_after.get())
            self.on_save(self.event)
            self.destroy()
        except Exception as e:
            print(f"Validation error: {e}")

class CDPActionDialog(BaseActionDialog):
    """Dialog for editing CDP Physical Input and NST Setup events with CSV mapping."""
    
    def __init__(self, master, event: MacroEvent, on_save: Callable[[MacroEvent], None], csv_engine=None):
        title = "🌐 Edit CDP Action" if event.event_type == EventType.CDP_PHYSICAL_INPUT else "🌐 Edit Profile Setup"
        if event.event_type == EventType.AI_CAPTCHA_SOLVE:
            title = "🤖 Edit AI Captcha Solve"
            
        super().__init__(master, event, on_save, title=title)
        self.csv_engine = csv_engine

        # Selector Field
        f_sel = ctk.CTkFrame(self.body, fg_color="transparent")
        f_sel.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(f_sel, text="CSS Selector:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_sel = ctk.CTkEntry(f_sel, width=200)
        self.ent_sel.insert(0, self.event.selector)
        self.ent_sel.pack(side="right")
        
        # Text/Value Mapping with CSV Dropdown
        f_text = ctk.CTkFrame(self.body, fg_color="transparent")
        f_text.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(f_text, text="Input Text/Value:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        
        self.ent_text = ctk.CTkEntry(f_text, width=200)
        self.ent_text.insert(0, self.event.text)
        self.ent_text.pack(side="right")
        
        if self.csv_engine and self.csv_engine.is_loaded:
            headers = self.csv_engine.get_headers()
            if headers:
                f_map = ctk.CTkFrame(self.body, fg_color="transparent")
                f_map.pack(fill="x", padx=16, pady=6)
                ctk.CTkLabel(f_map, text="Auto-Map CSV Column:", text_color=GlassTheme.ACCENT_CYAN).pack(side="left")
                
                self.opt_csv = ctk.CTkOptionMenu(f_map, values=["(Select)"] + headers, command=self._on_csv_select)
                self.opt_csv.pack(side="right")
                
        self._add_delay_and_policy_fields()

        # Optional Step Checkbox (for cookie banners, popups, disposable overlays)
        f_opt = ctk.CTkFrame(self.body, fg_color="transparent")
        f_opt.pack(fill="x", padx=16, pady=4)
        self.chk_optional = ctk.CTkCheckBox(
            f_opt,
            text="Optional (Continue if element is not on page)",
            font=ctk.CTkFont(size=11),
            text_color=GlassTheme.ACCENT_CYAN,
            command=self._on_optional_toggle
        )
        self.chk_optional.pack(side="left")
        if self.event.error_policy == ErrorPolicy.SKIP or any(term in self.event.selector.lower() for term in ["onetrust", "cookie", "consent", "modal", "alert"]):
            self.chk_optional.select()

        self._add_bottom_buttons(self._save)

    def _on_optional_toggle(self):
        if self.chk_optional.get():
            self.opt_error_policy.set("skip")
        else:
            self.opt_error_policy.set("stop")

    def _on_csv_select(self, choice: str):
        if choice != "(Select)":
            self.ent_text.delete(0, "end")
            self.ent_text.insert(0, f"{{{{{choice}}}}}")

    def _save(self):
        try:
            self.event.selector = self.ent_sel.get()
            self.event.text = self.ent_text.get()
            self.event.delay_after_ms = float(self.ent_delay_after.get())
            if self.chk_optional.get():
                self.event.error_policy = ErrorPolicy.SKIP
            else:
                self.event.error_policy = ErrorPolicy(self.opt_error_policy.get())
            self.on_save(self.event)
            self.destroy()
        except Exception as e:
            print(f"Validation error: {e}")
