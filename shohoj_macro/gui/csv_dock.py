"""
CSV Data Dock Panel & Variable Inspector (v2.0.0 Enterprise)
Provides dataset uploading, column badge inspection, and variable templating tools.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
from typing import Callable, Optional
from shohoj_macro.gui.glass_theme import GlassTheme, GlassCard, GlassButton, GlassTooltip
from shohoj_macro.core.csv_engine import CSVDataEngine
from shohoj_macro.gui.csv_viewer_window import CSVViewerWindow
from shohoj_macro.core.settings_manager import SettingsManager


class CSVDockPanel(GlassCard):
    """Sidebar dock managing CSV data loading and dynamic variable badges."""

    def __init__(self, master, csv_engine: CSVDataEngine, on_dataset_changed: Callable[[], None] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.csv_engine = csv_engine
        self.on_dataset_changed = on_dataset_changed

        self._build_ui()
        
        # Auto-load previous CSV
        state = SettingsManager().config.get("state", {})
        last_csv = state.get("last_csv_path")
        if last_csv and os.path.exists(last_csv):
            try:
                self.csv_engine.load_csv(last_csv)
                self.lbl_file_info.configure(
                    text=f"Loaded: {os.path.basename(last_csv)}\\nRows: {self.csv_engine.get_row_count()} | Cols: {len(self.csv_engine.headers)}",
                    text_color=GlassTheme.ACCENT_EMERALD
                )
                self._update_badges()
                if self.on_dataset_changed:
                    self.on_dataset_changed()
            except: pass

    def _build_ui(self):
        # Header
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            top_frame,
            text="📊 CSV Dataset Dock",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=12, weight="bold"),
            text_color=GlassTheme.ACCENT_EMERALD,
        ).pack(side="left")

        # Action Buttons
        self.btn_load = ctk.CTkButton(
            self,
            text="📁 Load CSV Dataset",
            height=28,
            corner_radius=6,
            fg_color="#143A22",
            hover_color=GlassTheme.ACCENT_EMERALD,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
            command=self._load_csv_file,
        )
        self.btn_load.pack(fill="x", padx=10, pady=3)
        GlassTooltip(self.btn_load, "Upload a CSV file for automated form filling and registration")

        # Status Card
        self.status_card = ctk.CTkFrame(self, fg_color="#10121A", corner_radius=6)
        self.status_card.pack(fill="x", padx=10, pady=4)

        self.lbl_file_info = ctk.CTkLabel(
            self.status_card,
            text="No CSV Loaded (Single Mode)",
            font=ctk.CTkFont(size=10),
            text_color=GlassTheme.TEXT_MUTED,
            wraplength=170,
        )
        self.lbl_file_info.pack(padx=8, pady=6)

        # Variables Badge Container
        self.badge_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.badge_frame.pack(fill="both", expand=True, padx=8, pady=2)

        # Bottom Tools: Preview Data & Clear
        self.bot_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bot_frame.pack(fill="x", padx=10, pady=(4, 8))

        self.btn_preview = ctk.CTkButton(
            self.bot_frame,
            text="👁️ View Data",
            width=75,
            height=24,
            corner_radius=6,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            font=ctk.CTkFont(size=10),
            state="disabled",
            command=self._open_data_viewer,
        )
        self.btn_preview.pack(side="left")

        self.btn_clear = ctk.CTkButton(
            self.bot_frame,
            text="✕ Clear",
            width=55,
            height=24,
            corner_radius=6,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color=GlassTheme.ACCENT_RED,
            font=ctk.CTkFont(size=10),
            state="disabled",
            command=self._clear_csv,
        )
        self.btn_clear.pack(side="right")

    def _load_csv_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return

        success, msg = self.csv_engine.load_file(path)
        if success:
            self._update_display()
            if self.on_dataset_changed:
                self.on_dataset_changed()
        else:
            messagebox.showerror("CSV Load Error", msg)

    def _clear_csv(self):
        self.csv_engine.clear()
        self._update_display()
        if self.on_dataset_changed:
            self.on_dataset_changed()

    def _update_display(self):
        # Clear old badges
        for child in self.badge_frame.winfo_children():
            child.destroy()

        if self.csv_engine.is_loaded:
            filename = os.path.basename(self.csv_engine.filepath)
            row_count = self.csv_engine.get_row_count()
            col_count = len(self.csv_engine.headers)

            self.lbl_file_info.configure(
                text=f"🟢 {filename}\n({row_count} rows • {col_count} columns)",
                text_color=GlassTheme.ACCENT_EMERALD,
            )
            self.btn_preview.configure(state="normal")
            self.btn_clear.configure(state="normal")

            # Add header badges
            ctk.CTkLabel(
                self.badge_frame,
                text="Click variable to copy:",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=GlassTheme.TEXT_SECONDARY,
            ).pack(anchor="w", pady=(2, 4))

            scroll_box = ctk.CTkScrollableFrame(self.badge_frame, fg_color="transparent", height=90)
            scroll_box.pack(fill="both", expand=True)

            for h in self.csv_engine.headers:
                var_tag = f"{{{{{h}}}}}"
                btn = ctk.CTkButton(
                    scroll_box,
                    text=var_tag,
                    height=22,
                    corner_radius=4,
                    fg_color="#182436",
                    hover_color=GlassTheme.ACCENT_BLUE,
                    text_color=GlassTheme.ACCENT_CYAN,
                    font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
                    command=lambda v=var_tag: self._copy_variable(v),
                )
                btn.pack(fill="x", pady=1)
                GlassTooltip(btn, f"Copy {var_tag} to clipboard for typing actions")
        else:
            self.lbl_file_info.configure(
                text="No CSV Loaded (Single Mode)",
                text_color=GlassTheme.TEXT_MUTED,
            )
            self.btn_preview.configure(state="disabled")
            self.btn_clear.configure(state="disabled")

    def _copy_variable(self, var_str: str):
        self.clipboard_clear()
        self.clipboard_append(var_str)
        self.update()

    def _open_data_viewer(self):
        if not self.csv_engine.is_loaded:
            return
        CSVViewerWindow(self, self.csv_engine)
