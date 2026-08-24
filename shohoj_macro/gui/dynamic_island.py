"""
Apple-Style Dynamic Island Floating Mini-HUD (v2.0.0 Hardware Anti-Aliased)
True geometric rounded pill shape with zero black borders, live status proof, and 1-click Studio window switcher.
"""

import ctypes
from ctypes import wintypes
import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional
from shohoj_macro.gui.glass_theme import GlassTheme

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
GA_ROOT = 2


class DynamicIslandHUD(ctk.CTkToplevel):
    """Floating top-of-screen Dynamic Island mini HUD with hardware rounded corners and Studio switcher."""

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

        # Geometry
        screen_w = self.winfo_screenwidth()
        self.hud_w = 420
        self.hud_h = 42
        pos_x = int((screen_w - self.hud_w) / 2)
        pos_y = 16
        self.geometry(f"{self.hud_w}x{self.hud_h}+{pos_x}+{pos_y}")

        # Configure window: frameless, topmost, transparent background color key
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.config(bg="#010203")
        try:
            self.wm_attributes("-transparentcolor", "#010203")
        except Exception:
            pass

        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()
        self.bind("<ButtonPress-1>", self._start_drag)
        self.bind("<B1-Motion>", self._do_drag)

        # Apply native geometric Win32 RoundRect region to guarantee 0 black corners
        self.after(20, self._apply_hardware_pill_region)
        self.bind("<Configure>", lambda e: self._apply_hardware_pill_region())

    def _apply_hardware_pill_region(self):
        """Clips the OS window itself into a true geometric pill shape."""
        try:
            w = self.winfo_width() or self.hud_w
            h = self.winfo_height() or self.hud_h
            child_hwnd = self.winfo_id()
            root_hwnd = user32.GetAncestor(child_hwnd, GA_ROOT) or child_hwnd
            # Create smooth rounded rectangle region
            hrgn = gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, h, h)
            user32.SetWindowRgn(root_hwnd, hrgn, True)
        except Exception:
            pass

    def _build_ui(self):
        self.capsule = ctk.CTkFrame(
            self,
            fg_color="#101320",
            border_color=GlassTheme.ACCENT_CYAN,
            border_width=1.5,
            corner_radius=21,
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

        # Brand / Status Label (Clicking restores Studio window!)
        self.status_label = ctk.CTkButton(
            self.capsule,
            text="⚡ Shohoj Macro • Ready",
            text_color=GlassTheme.TEXT_PRIMARY,
            hover_color="#1A2035",
            fg_color="transparent",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
            height=26,
            command=self._restore_studio,
        )
        self.status_label.pack(side="left", padx=2)

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

        # Switch to Studio Button
        self.btn_studio = ctk.CTkButton(
            self.capsule,
            text="🗖 Studio",
            width=62,
            height=24,
            corner_radius=12,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#2E3754",
            text_color=GlassTheme.TEXT_PRIMARY,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=10, weight="bold"),
            command=self._restore_studio,
        )
        self.btn_studio.pack(side="right", padx=2)

        # Stop Button
        self.btn_stop = ctk.CTkButton(
            self.capsule,
            text="⏹ Stop",
            width=62,
            height=24,
            corner_radius=12,
            fg_color="#3A181C",
            hover_color=GlassTheme.ACCENT_RED,
            text_color=GlassTheme.ACCENT_RED,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=10, weight="bold"),
            command=self._on_stop_click,
        )
        self.btn_stop.pack(side="right", padx=2)

        # Play/Pause Action Button
        self.btn_action = ctk.CTkButton(
            self.capsule,
            text="▶ Play",
            width=54,
            height=24,
            corner_radius=12,
            fg_color="#182A3A",
            hover_color=GlassTheme.ACCENT_BLUE,
            text_color=GlassTheme.ACCENT_CYAN,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=10, weight="bold"),
            command=self._on_action_click,
        )
        self.btn_action.pack(side="right", padx=2)

    def _restore_studio(self):
        """Brings the main Shohoj Macro Studio window to the front."""
        if self.master:
            try:
                self.master.deiconify()
                self.master.state("normal")
                self.master.lift()
                self.master.focus_force()
            except Exception:
                pass

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
            txt = f"REC"
            if count > 0:
                txt += f" ({count})"
            if detail:
                txt += f" • {detail}"
            self.status_label.configure(text=f"● {txt}")
            self.btn_action.configure(text="⏹ Rec", fg_color="#3A181C", text_color=GlassTheme.ACCENT_RED)
        elif state == "PLAYING":
            self.capsule.configure(border_color=GlassTheme.ACCENT_EMERALD)
            self.status_dot.configure(text_color=GlassTheme.ACCENT_EMERALD)
            txt = f"PLAYING {detail}" if detail else "PLAYING"
            self.status_label.configure(text=f"▶ {txt}")
            self.btn_action.configure(text="⏸ Pause", fg_color="#3A2814", text_color=GlassTheme.ACCENT_ORANGE)
        elif state == "PAUSED":
            self.capsule.configure(border_color=GlassTheme.ACCENT_ORANGE)
            self.status_dot.configure(text_color=GlassTheme.ACCENT_ORANGE)
            self.status_label.configure(text="⏸ PAUSED")
            self.btn_action.configure(text="▶ Resume", fg_color="#182A3A", text_color=GlassTheme.ACCENT_CYAN)
        else:
            self.capsule.configure(border_color=GlassTheme.ACCENT_CYAN)
            self.status_dot.configure(text_color=GlassTheme.ACCENT_CYAN)
            self.status_label.configure(text="⚡ Shohoj Macro • Ready")
            self.btn_action.configure(text="▶ Play", fg_color="#182A3A", text_color=GlassTheme.ACCENT_CYAN)

    def _on_action_click(self):
        if self.on_toggle_play:
            self.on_toggle_play()

    def _on_stop_click(self):
        if self.on_stop:
            self.on_stop()
