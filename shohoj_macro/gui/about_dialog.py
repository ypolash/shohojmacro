"""
About & Developer Credits Dialog
"""

import customtkinter as ctk
from shohoj_macro.gui.glass_theme import GlassTheme, GlassButton
from shohoj_macro.version import (
    __app_name__,
    __version__,
    __edition__,
    __author__,
    __username__,
    __github__,
    __description__,
)


class AboutDialog(ctk.CTkToplevel):
    """About & branding window."""

    def __init__(self, master):
        super().__init__(master)
        self.title("About Shohoj Macro")
        self.geometry("440x420")
        self.configure(fg_color=GlassTheme.BG_DARK)
        self.attributes("-topmost", True)
        self.grab_set()

        self.body = ctk.CTkFrame(self, fg_color=GlassTheme.CARD_BG, corner_radius=14)
        self.body.pack(fill="both", expand=True, padx=16, pady=16)

        # Logo & App Title
        ctk.CTkLabel(
            self.body,
            text=f"⚡ {__app_name__}",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=18, weight="bold"),
            text_color=GlassTheme.ACCENT_CYAN,
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            self.body,
            text=f"Version {__version__} ({__edition__})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=GlassTheme.ACCENT_EMERALD,
        ).pack(pady=(0, 10))

        # Description
        ctk.CTkLabel(
            self.body,
            text=__description__,
            font=ctk.CTkFont(size=11),
            text_color=GlassTheme.TEXT_SECONDARY,
            wraplength=360,
            justify="center",
        ).pack(padx=16, pady=(0, 14))

        # Developer Info Box
        dev_box = ctk.CTkFrame(self.body, fg_color=GlassTheme.CARD_BG_SECONDARY, corner_radius=10)
        dev_box.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(
            dev_box,
            text="👨‍💻 Lead Architect & Developer",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=GlassTheme.TEXT_PRIMARY,
        ).pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            dev_box,
            text=f"Polash Khan ({__username__})",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=GlassTheme.ACCENT_CYAN,
        ).pack(anchor="w", padx=12, pady=(0, 2))

        ctk.CTkLabel(
            dev_box,
            text=f"GitHub: {__github__}",
            font=ctk.CTkFont(size=10),
            text_color=GlassTheme.TEXT_MUTED,
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Close Button
        GlassButton(
            self.body,
            text="Close",
            accent_color=GlassTheme.CARD_BORDER_GLOW,
            width=90,
            command=self.destroy,
        ).pack(side="bottom", pady=14)
