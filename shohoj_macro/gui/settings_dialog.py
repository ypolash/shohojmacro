"""
Settings & Preferences Dialog
Configures Global Hotkeys, Humanizer Presets, Anti-Detection & Error Policies.
"""

import customtkinter as ctk
from typing import Callable
from shohoj_macro.gui.glass_theme import GlassTheme, GlassButton


class SettingsDialog(ctk.CTkToplevel):
    """Settings modal window."""

    def __init__(self, master, current_settings: dict, on_save: Callable[[dict], None]):
        super().__init__(master)
        self.settings = dict(current_settings)
        self.on_save = on_save

        self.title("⚙️ Shohoj Macro - Preferences")
        self.geometry("480x520")
        self.configure(fg_color=GlassTheme.BG_DARK)
        self.attributes("-topmost", True)
        self.grab_set()

        self.body = ctk.CTkFrame(self, fg_color=GlassTheme.CARD_BG, corner_radius=14)
        self.body.pack(fill="both", expand=True, padx=16, pady=16)

        # Title
        ctk.CTkLabel(
            self.body,
            text="Preferences & Configuration",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=15, weight="bold"),
            text_color=GlassTheme.ACCENT_CYAN,
        ).pack(pady=(14, 12))

        # 1. Hotkeys Section
        ctk.CTkLabel(self.body, text="Global Hotkeys", font=ctk.CTkFont(size=12, weight="bold"), text_color=GlassTheme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(4, 2))

        f_hk1 = ctk.CTkFrame(self.body, fg_color="transparent")
        f_hk1.pack(fill="x", padx=16, pady=2)
        ctk.CTkLabel(f_hk1, text="Record / Stop Hotkey:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_rec_key = ctk.CTkEntry(f_hk1, width=100)
        self.ent_rec_key.insert(0, self.settings.get("record_hotkey", "<f8>"))
        self.ent_rec_key.pack(side="right")

        f_hk2 = ctk.CTkFrame(self.body, fg_color="transparent")
        f_hk2.pack(fill="x", padx=16, pady=2)
        ctk.CTkLabel(f_hk2, text="Play / Pause Hotkey:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_play_key = ctk.CTkEntry(f_hk2, width=100)
        self.ent_play_key.insert(0, self.settings.get("play_hotkey", "<f9>"))
        self.ent_play_key.pack(side="right")

        f_hk3 = ctk.CTkFrame(self.body, fg_color="transparent")
        f_hk3.pack(fill="x", padx=16, pady=2)
        ctk.CTkLabel(f_hk3, text="Emergency Kill Switch:", text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.ent_stop_key = ctk.CTkEntry(f_hk3, width=100)
        self.ent_stop_key.insert(0, self.settings.get("stop_hotkey", "<f10>"))
        self.ent_stop_key.pack(side="right")

        # 2. Humanizer & Stealth Section
        ctk.CTkLabel(self.body, text="StealthCore & Humanizer Physics", font=ctk.CTkFont(size=12, weight="bold"), text_color=GlassTheme.TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(12, 2))

        self.chk_humanizer = ctk.CTkCheckBox(self.body, text="Enable WindMouse & Natural Bézier Curves")
        if self.settings.get("humanizer_enabled", True):
            self.chk_humanizer.select()
        self.chk_humanizer.pack(anchor="w", padx=16, pady=4)

        self.chk_biorhythm = ctk.CTkCheckBox(self.body, text="Enable Bio-Rhythm Fatigue & Micro-Hesitations")
        if self.settings.get("bio_rhythm_enabled", True):
            self.chk_biorhythm.select()
        self.chk_biorhythm.pack(anchor="w", padx=16, pady=4)

        self.chk_block_input = ctk.CTkCheckBox(self.body, text="Shield Physical Input during Playback (BlockInput)")
        if self.settings.get("block_physical_input", False):
            self.chk_block_input.select()
        self.chk_block_input.pack(anchor="w", padx=16, pady=4)

        # Bottom Buttons
        btn_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=16, pady=14)

        ctk.CTkButton(btn_frame, text="Cancel", fg_color=GlassTheme.CARD_BG_SECONDARY, hover_color="#333A4D", width=80, command=self.destroy).pack(side="left")
        GlassButton(btn_frame, text="Apply Settings", accent_color=GlassTheme.ACCENT_BLUE, width=120, command=self._save).pack(side="right")

    def _save(self):
        self.settings["record_hotkey"] = self.ent_rec_key.get()
        self.settings["play_hotkey"] = self.ent_play_key.get()
        self.settings["stop_hotkey"] = self.ent_stop_key.get()
        self.settings["humanizer_enabled"] = bool(self.chk_humanizer.get())
        self.settings["bio_rhythm_enabled"] = bool(self.chk_biorhythm.get())
        self.settings["block_physical_input"] = bool(self.chk_block_input.get())

        if self.on_save:
            self.on_save(self.settings)
        self.destroy()
