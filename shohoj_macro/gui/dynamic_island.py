"""
Apple-Style Dynamic Island Floating Mini-HUD (v2.0.0 Hardware Anti-Aliased)
Presents live visual proof of recording, live action count, and playback progress with zero black borders.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional
from shohoj_macro.gui.glass_theme import GlassTheme
from shohoj_macro.utils.win32_input import set_dwm_rounded_corners


class DynamicIslandHUD(ctk.CTkToplevel):
    """Floating top-of-screen Dynamic Island mini HUD with hardware rounded corners."""

    def __init__(
        self,
        master,
        on_toggle_record: Callable = None,
        on_toggle_play: Callable = None,
        on_stop: Callable = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_toggle_record = on_toggle_record
        self.on_toggle_play = on_toggle_play
        self.on_stop = on_stop

        # Configure window as frameless, topmost, transparent-keyed floating pill
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.config(bg="#0B0C10")

        # Geometry
        screen_w = self.winfo_screenwidth()
        hud_w = 400
        hud_h = 42
        pos_x = int((screen_w - hud_w) / 2)
        pos_y = 16
        self.geometry(f"{hud_w}x{hud_h}+{pos_x}+{pos_y}")

        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()
        self.bind("<ButtonPress-1>", self._start_drag)
        self.bind("<B1-Motion>", self._do_drag)

        # Apply Windows 11 DWM native hardware anti-aliasing
        self.after(50, self._apply_dwm_styling)

    def _apply_dwm_styling(self):
        try:
            hwnd = self.winfo_id()
            # Try to get top-level hwnd
            import ctypes
            user32 = ctypes.windll.user32
            parent_hwnd = user32.GetParent(hwnd) or hwnd
            set_dwm_rounded_corners(parent_hwnd)
        except Exception:
            pass

    def _build_ui(self):
        self.capsule = ctk.CTkFrame(
            self,
            fg_color="#121522",
            border_color=GlassTheme.ACCENT_CYAN,
            border_width=1,
            corner_radius=20,
        )
        self.capsule.pack(fill="both", expand=True, padx=1, pady=1)

        # Status Dot (Pulsing Indicator)
        self.status_dot = ctk.CTkLabel(
            self.capsule,
            text="●",
            text_color=GlassTheme.ACCENT_CYAN,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=18,
        )
        self.status_dot.pack(side="left", padx=(12, 0))

        # Status Label & Action Count
        self.status_label = ctk.CTkLabel(
            self.capsule,
            text="Shohoj Macro • Ready",
            text_color=GlassTheme.TEXT_PRIMARY,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
        )
        self.status_label.pack(side="left", padx=4)

        # Close / Dismiss Button
        self.btn_close = ctk.CTkButton(
            self.capsule,
            text="✕",
            width=20,
            height=20,
            corner_radius=10,
            fg_color="transparent",
            hover_color="#2A161A",
            text_color=GlassTheme.TEXT_MUTED,
            font=ctk.CTkFont(size=9, weight="bold"),
            command=self.destroy,
        )
        self.btn_close.pack(side="right", padx=(2, 8))

        # Stop Button
        self.btn_stop = ctk.CTkButton(
            self.capsule,
            text="⏹ Stop",
            width=68,
            height=24,
            corner_radius=12,
            fg_color="#3A181C",
            hover_color=GlassTheme.ACCENT_RED,
            text_color=GlassTheme.ACCENT_RED,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=10, weight="bold"),
            command=self._on_stop_click,
        )
        self.btn_stop.pack(side="right", padx=3)

        # Play/Pause Action Button
        self.btn_action = ctk.CTkButton(
            self.capsule,
            text="▶ Play",
            width=58,
            height=24,
            corner_radius=12,
            fg_color="#182A3A",
            hover_color=GlassTheme.ACCENT_BLUE,
            text_color=GlassTheme.ACCENT_CYAN,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=10, weight="bold"),
            command=self._on_action_click,
        )
        self.btn_action.pack(side="right", padx=2)

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _do_drag(self, event):
        x = self.winfo_x() - self._drag_start_x + event.x
        y = self.winfo_y() - self._drag_start_y + event.y
        self.geometry(f"+{x}+{y}")

    def update_status(self, state: str, detail: str = "", count: int = 0):
        """Updates Dynamic Island live indicator and action count."""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        if state == "RECORDING":
            self.capsule.configure(border_color=GlassTheme.ACCENT_RED)
            self.status_dot.configure(text_color=GlassTheme.ACCENT_RED)
            txt = f"RECORDING"
            if count > 0:
                txt += f" ({count})"
            if detail:
                txt += f" • {detail}"
            self.status_label.configure(text=txt)
            self.btn_action.configure(text="⏹ Rec", fg_color="#3A181C", text_color=GlassTheme.ACCENT_RED)
        elif state == "PLAYING":
            self.capsule.configure(border_color=GlassTheme.ACCENT_EMERALD)
            self.status_dot.configure(text_color=GlassTheme.ACCENT_EMERALD)
            txt = f"PLAYING {detail}" if detail else "PLAYING"
            self.status_label.configure(text=txt)
            self.btn_action.configure(text="⏸ Pause", fg_color="#3A2814", text_color=GlassTheme.ACCENT_ORANGE)
        elif state == "PAUSED":
            self.capsule.configure(border_color=GlassTheme.ACCENT_ORANGE)
            self.status_dot.configure(text_color=GlassTheme.ACCENT_ORANGE)
            self.status_label.configure(text="PAUSED")
            self.btn_action.configure(text="▶ Resume", fg_color="#182A3A", text_color=GlassTheme.ACCENT_CYAN)
        else:
            self.capsule.configure(border_color=GlassTheme.ACCENT_CYAN)
            self.status_dot.configure(text_color=GlassTheme.ACCENT_CYAN)
            self.status_label.configure(text="Shohoj Macro • Ready")
            self.btn_action.configure(text="▶ Play", fg_color="#182A3A", text_color=GlassTheme.ACCENT_CYAN)

    def _on_action_click(self):
        if self.on_toggle_play:
            self.on_toggle_play()

    def _on_stop_click(self):
        if self.on_stop:
            self.on_stop()
