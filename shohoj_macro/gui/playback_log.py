"""
Ring-Buffered Real-Time Execution Log
Displays timestamped macro execution activity with color-coded badges.
"""

import tkinter as tk
import customtkinter as ctk
from datetime import datetime
from shohoj_macro.gui.glass_theme import GlassTheme, GlassCard


class PlaybackLogPanel(GlassCard):
    """Execution log with rolling ring buffer to avoid memory leaks."""

    def __init__(self, master, max_lines: int = 500, **kwargs):
        super().__init__(master, **kwargs)
        self.max_lines = max_lines

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=12, pady=(10, 4))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="📋 Execution & Activity Log",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=12, weight="bold"),
            text_color=GlassTheme.TEXT_PRIMARY,
        )
        self.title_label.pack(side="left")

        self.btn_clear = ctk.CTkButton(
            self.header_frame,
            text="Clear",
            width=48,
            height=22,
            corner_radius=6,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            font=ctk.CTkFont(size=10),
            command=self.clear,
        )
        self.btn_clear.pack(side="right")

        # Text Widget
        self.text_widget = tk.Text(
            self,
            bg=GlassTheme.BG_DARK,
            fg=GlassTheme.TEXT_PRIMARY,
            insertbackground="#FFFFFF",
            font=("Consolas", 9),
            wrap="word",
            bd=0,
            highlightthickness=0,
        )
        self.text_widget.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Tag configurations
        self.text_widget.tag_config("time", foreground="#5E667E")
        self.text_widget.tag_config("INFO", foreground="#00F0FF")
        self.text_widget.tag_config("WARN", foreground="#FF9F0A")
        self.text_widget.tag_config("ERROR", foreground="#FF453A")
        self.text_widget.tag_config("SUCCESS", foreground="#30D158")

        self._line_count = 0

    def log(self, message: str, level: str = "INFO"):
        """Appends a new line to the execution log."""
        self.text_widget.config(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        self.text_widget.insert("end", f"[{timestamp}] ", "time")
        self.text_widget.insert("end", f"[{level}] ", level)
        self.text_widget.insert("end", f"{message}\n")

        self._line_count += 1
        if self._line_count > self.max_lines:
            # Delete oldest line
            self.text_widget.delete("1.0", "2.0")
            self._line_count -= 1

        self.text_widget.see("end")
        self.text_widget.config(state="disabled")

    def clear(self):
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self._line_count = 0
        self.text_widget.config(state="disabled")
