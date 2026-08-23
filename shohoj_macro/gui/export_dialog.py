"""
Export Format Selector & Feature Matrix Dialog
"""

import customtkinter as ctk
from typing import Callable
from shohoj_macro.gui.glass_theme import GlassTheme, GlassButton


class ExportDialog(ctk.CTkToplevel):
    """Export modal with format selection and feature comparison."""

    def __init__(self, master, on_export_selected: Callable[[str], None]):
        super().__init__(master)
        self.on_export_selected = on_export_selected

        self.title("📤 Export Macro Script")
        self.geometry("460x360")
        self.configure(fg_color=GlassTheme.BG_DARK)
        self.attributes("-topmost", True)
        self.grab_set()

        self.body = ctk.CTkFrame(self, fg_color=GlassTheme.CARD_BG, corner_radius=14)
        self.body.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            self.body,
            text="Choose Export Format",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=15, weight="bold"),
            text_color=GlassTheme.ACCENT_CYAN,
        ).pack(pady=(14, 8))

        # Python Card
        self.card_py = ctk.CTkFrame(self.body, fg_color=GlassTheme.CARD_BG_SECONDARY, corner_radius=10)
        self.card_py.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(self.card_py, text="🐍 Standalone Python Script (.py)", font=ctk.CTkFont(size=12, weight="bold"), text_color=GlassTheme.ACCENT_EMERALD).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(self.card_py, text="Full fidelity (~95% parity). Includes embedded WindMouse physics & high-res timing.", font=ctk.CTkFont(size=10), text_color=GlassTheme.TEXT_SECONDARY, wraplength=380, justify="left").pack(anchor="w", padx=12, pady=(0, 6))
        GlassButton(self.card_py, text="Export as Python (.py)", accent_color=GlassTheme.ACCENT_BLUE, height=26, command=lambda: self._export("python")).pack(anchor="e", padx=12, pady=(0, 8))

        # AHK Card
        self.card_ahk = ctk.CTkFrame(self.body, fg_color=GlassTheme.CARD_BG_SECONDARY, corner_radius=10)
        self.card_ahk.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(self.card_ahk, text="📜 AutoHotkey Script (.ahk)", font=ctk.CTkFont(size=12, weight="bold"), text_color=GlassTheme.ACCENT_ORANGE).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(self.card_ahk, text="Basic export (~40% parity). Linear mouse moves and fixed delays. No WindMouse.", font=ctk.CTkFont(size=10), text_color=GlassTheme.TEXT_SECONDARY, wraplength=380, justify="left").pack(anchor="w", padx=12, pady=(0, 6))
        GlassButton(self.card_ahk, text="Export as AHK (.ahk)", accent_color=GlassTheme.CARD_BORDER_GLOW, height=26, command=lambda: self._export("ahk")).pack(anchor="e", padx=12, pady=(0, 8))

    def _export(self, fmt: str):
        if self.on_export_selected:
            self.on_export_selected(fmt)
        self.destroy()
