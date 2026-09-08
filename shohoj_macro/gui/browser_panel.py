"""
Browser Companion Status & DOM Inspector Controller Panel
"""

import customtkinter as ctk
from typing import Callable
from shohoj_macro.gui.glass_theme import GlassTheme, GlassCard, GlassButton


class BrowserCompanionPanel(GlassCard):
    """Panel showing WebSocket bridge status and web inspection controls."""

    def __init__(
        self,
        master,
        on_inspect_web_element: Callable = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_inspect_web_element = on_inspect_web_element

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            self.header,
            text="🌐 Browser Companion (MV3)",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=12, weight="bold"),
            text_color=GlassTheme.TEXT_PRIMARY,
        ).pack(side="left")

        # Status Pill
        self.status_pill = ctk.CTkLabel(
            self.header,
            text="Disconnected",
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color="#3A181C",
            text_color=GlassTheme.ACCENT_RED,
            corner_radius=10,
            padx=8,
            pady=2,
        )
        self.status_pill.pack(side="right")

        # Description
        ctk.CTkLabel(
            self,
            text="Bypasses Cloudflare & Bot Protection.",
            font=ctk.CTkFont(size=10),
            text_color=GlassTheme.TEXT_SECONDARY,
            wraplength=260,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(2, 8))

        # Inspect Button
        self.btn_inspect = GlassButton(
            self,
            text="🎯 Pick Web Element via Browser",
            accent_color=GlassTheme.ACCENT_CYAN,
            command=self._on_inspect_click,
            height=28,
        )
        self.btn_inspect.pack(fill="x", padx=12, pady=(0, 10))

    def set_connected(self, connected: bool):
        if connected:
            self.status_pill.configure(text="Connected (Port 8765)", fg_color="#143A22", text_color=GlassTheme.ACCENT_EMERALD)
        else:
            self.status_pill.configure(text="Disconnected", fg_color="#3A181C", text_color=GlassTheme.ACCENT_RED)

    def _on_inspect_click(self):
        if self.on_inspect_web_element:
            self.on_inspect_web_element()
