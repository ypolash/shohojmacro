"""
Sidebar Macro Library, File Browser & Tag Search
"""

import customtkinter as ctk
from typing import Callable
from shohoj_macro.core.storage import MacroStorage
from shohoj_macro.gui.glass_theme import GlassTheme, GlassCard


class MacroLibrarySidebar(GlassCard):
    """Sidebar for managing saved macros and templates."""

    def __init__(
        self,
        master,
        on_macro_selected: Callable[[str], None] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_macro_selected = on_macro_selected

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            self.header,
            text="📁 Macro Library",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=12, weight="bold"),
            text_color=GlassTheme.TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            self.header,
            text="🔄",
            width=24,
            height=24,
            corner_radius=6,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            command=self.refresh_library,
        ).pack(side="right")

        # Search Bar
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Search macros...",
            height=28,
            corner_radius=8,
            fg_color=GlassTheme.BG_DARK,
            border_color=GlassTheme.CARD_BORDER,
        )
        self.search_entry.pack(fill="x", padx=10, pady=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_macros())

        # Scrollable Macro List
        self.scroll_list = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.scroll_list.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        self._all_macros = []
        self.refresh_library()

    def refresh_library(self):
        """Scans folder and re-populates macro cards."""
        for w in self.scroll_list.winfo_children():
            w.destroy()

        self._all_macros = MacroStorage.list_library_macros()
        self._filter_macros()

    def _filter_macros(self):
        query = self.search_entry.get().strip().lower()
        for w in self.scroll_list.winfo_children():
            w.destroy()

        matched = [
            m for m in self._all_macros
            if query in m["name"].lower() or any(query in t.lower() for t in m.get("tags", []))
        ]

        if not matched:
            ctk.CTkLabel(
                self.scroll_list,
                text="No saved macros found.",
                font=ctk.CTkFont(size=10),
                text_color=GlassTheme.TEXT_MUTED,
            ).pack(pady=12)
            return

        for item in matched:
            card = ctk.CTkFrame(
                self.scroll_list,
                fg_color=GlassTheme.CARD_BG_SECONDARY,
                border_color=GlassTheme.CARD_BORDER,
                border_width=1,
                corner_radius=8,
            )
            card.pack(fill="x", pady=3, padx=2)

            lbl_name = ctk.CTkLabel(
                card,
                text=item["name"],
                font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
                text_color=GlassTheme.TEXT_PRIMARY,
                anchor="w",
            )
            lbl_name.pack(fill="x", padx=8, pady=(4, 0))

            lbl_info = ctk.CTkLabel(
                card,
                text=f"{item['event_count']} actions",
                font=ctk.CTkFont(size=9),
                text_color=GlassTheme.TEXT_MUTED,
                anchor="w",
            )
            lbl_info.pack(fill="x", padx=8, pady=(0, 4))

            # Bind click
            path = item["path"]
            card.bind("<Button-1>", lambda e, p=path: self._on_item_click(p))
            lbl_name.bind("<Button-1>", lambda e, p=path: self._on_item_click(p))
            lbl_info.bind("<Button-1>", lambda e, p=path: self._on_item_click(p))

    def _on_item_click(self, path: str):
        if self.on_macro_selected:
            self.on_macro_selected(path)
