"""
Apple-Style Dynamic Island Floating Mini-HUD Widget
Presents live on-screen visual proof of recording, live action count, and playback progress.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Callable
from shohoj_macro.gui.glass_theme import GlassTheme


class DynamicIslandHUD(ctk.CTkToplevel):
    """Floating top-of-screen Dynamic Island mini HUD."""

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
        self.config(bg="#010204")
        self.wm_attributes("-transparentcolor", "#010204")

        # Geometry
        screen_w = self.winfo_screenwidth()
        hud_w = 380
        hud_h = 46
        pos_x = int((screen_w - hud_w) / 2)
        pos_y = 18
        self.geometry(f"{hud_w}x{hud_h}+{pos_x}+{pos_y}")

        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()
        self.bind("<ButtonPress-1>", self._start_drag)
        self.bind("<B1-Motion>", self._do_drag)

    def _build_ui(self):
        self.capsule = ctk.CTkFrame(
            self,
            fg_color="#10121A",
            border_color=GlassTheme.CARD_BORDER_GLOW,
            border_width=1.5,
            corner_radius=23,
        )
        self.capsule.pack(fill="both", expand=True, padx=2, pady=2)

        # Status Dot (Pulsing Indicator)
        self.status_dot = ctk.CTkLabel(
            self.capsule,
            text="●",
            text_color=GlassTheme.ACCENT_CYAN,
            font=ctk.CTkFont(size=15, weight="bold"),
            width=20,
        )
        self.status_dot.pack(side="left", padx=(12, 2))

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
            width=22,
            height=22,
            corner_radius=11,
            fg_color="transparent",
            hover_color="#2A161A",
            text_color=GlassTheme.TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self.destroy,
        )
        self.btn_close.pack(side="right", padx=(2, 10))

        # Stop Button
        self.btn_stop = ctk.CTkButton(
            self.capsule,
            text="⏹ Stop (F10)",
            width=76,
            height=26,
            corner_radius=13,
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
            height=26,
            corner_radius=13,
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
            self.status_dot.configure(text_color=GlassTheme.ACCENT_RED)
            txt = f"RECORDING"
            if count > 0:
                txt += f" ({count} actions)"
            if detail:
                txt += f" • {detail}"
            self.status_label.configure(text=txt)
            self.btn_action.configure(text="⏹ Rec", fg_color="#3A181C", text_color=GlassTheme.ACCENT_RED)
        elif state == "PLAYING":
            self.status_dot.configure(text_color=GlassTheme.ACCENT_EMERALD)
            txt = f"PLAYING {detail}" if detail else "PLAYING"
            self.status_label.configure(text=txt)
            self.btn_action.configure(text="⏸ Pause", fg_color="#3A2814", text_color=GlassTheme.ACCENT_ORANGE)
        elif state == "PAUSED":
            self.status_dot.configure(text_color=GlassTheme.ACCENT_ORANGE)
            self.status_label.configure(text="PAUSED")
            self.btn_action.configure(text="▶ Resume", fg_color="#182A3A", text_color=GlassTheme.ACCENT_CYAN)
        else:
            self.status_dot.configure(text_color=GlassTheme.ACCENT_CYAN)
            self.status_label.configure(text="Shohoj Macro • Ready")
            self.btn_action.configure(text="▶ Play", fg_color="#182A3A", text_color=GlassTheme.ACCENT_CYAN)

    def _on_action_click(self):
        if self.on_toggle_play:
            self.on_toggle_play()

    def _on_stop_click(self):
        if self.on_stop:
            self.on_stop()
