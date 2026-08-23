"""
Interactive Visual Timeline & Step-by-Step Action Table Editor
Provides drag-and-drop / ordering, inline enable/disable, and quick action modifiers.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Callable, Optional
from shohoj_macro.core.events import MacroEvent, EventType
from shohoj_macro.gui.glass_theme import GlassTheme, GlassCard, GlassButton
from shohoj_macro.gui.action_dialogs import MouseActionDialog, DelayActionDialog, TextTypeActionDialog


class TimelineTableEditor(GlassCard):
    """Visual table editor for macro action sequences."""

    def __init__(
        self,
        master,
        on_events_modified: Callable[[], None] = None,
        on_step_selected: Callable[[int], None] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_events_modified = on_events_modified
        self.on_step_selected = on_step_selected
        self.events: list[MacroEvent] = []

        self._build_toolbar()
        self._build_table()

    def _build_toolbar(self):
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.pack(fill="x", padx=12, pady=(10, 6))

        # Title
        ctk.CTkLabel(
            self.toolbar,
            text="⚡ Action Sequence Timeline",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=13, weight="bold"),
            text_color=GlassTheme.TEXT_PRIMARY,
        ).pack(side="left")

        # Action Buttons (Right Aligned)
        btn_cfg = {"width": 32, "height": 26, "corner_radius": 6, "font": ctk.CTkFont(size=11, weight="bold")}

        self.btn_del = ctk.CTkButton(
            self.toolbar,
            text="🗑️",
            fg_color="#3A181C",
            hover_color=GlassTheme.ACCENT_RED,
            command=self._delete_selected,
            **btn_cfg,
        )
        self.btn_del.pack(side="right", padx=2)

        self.btn_dup = ctk.CTkButton(
            self.toolbar,
            text="📋",
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            command=self._duplicate_selected,
            **btn_cfg,
        )
        self.btn_dup.pack(side="right", padx=2)

        self.btn_down = ctk.CTkButton(
            self.toolbar,
            text="▼",
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            command=self._move_down,
            **btn_cfg,
        )
        self.btn_down.pack(side="right", padx=2)

        self.btn_up = ctk.CTkButton(
            self.toolbar,
            text="▲",
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            command=self._move_up,
            **btn_cfg,
        )
        self.btn_up.pack(side="right", padx=2)

        self.btn_edit = ctk.CTkButton(
            self.toolbar,
            text="✏️",
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color=GlassTheme.ACCENT_CYAN,
            command=self._edit_selected,
            **btn_cfg,
        )
        self.btn_edit.pack(side="right", padx=2)

        self.btn_add = ctk.CTkButton(
            self.toolbar,
            text="➕",
            fg_color="#182A3A",
            hover_color=GlassTheme.ACCENT_BLUE,
            command=self._add_action_popup,
            **btn_cfg,
        )
        self.btn_add.pack(side="right", padx=2)

    def _build_table(self):
        # Frame for Treeview + Scrollbar
        table_frame = tk.Frame(self, bg=GlassTheme.BG_DARK)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=GlassTheme.BG_DARK,
            foreground="#FFFFFF",
            rowheight=26,
            fieldbackground=GlassTheme.BG_DARK,
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        style.map(
            "Treeview",
            background=[("selected", "#1A2B4D")],
            foreground=[("selected", GlassTheme.ACCENT_CYAN)],
        )
        style.configure(
            "Treeview.Heading",
            background=GlassTheme.CARD_BG,
            foreground=GlassTheme.TEXT_SECONDARY,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )

        columns = ("step", "type", "summary", "delay", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("step", text="#")
        self.tree.column("step", width=40, anchor="center")

        self.tree.heading("type", text="Type")
        self.tree.column("type", width=95, anchor="w")

        self.tree.heading("summary", text="Action Parameters & Details")
        self.tree.column("summary", width=340, anchor="w")

        self.tree.heading("delay", text="Delay")
        self.tree.column("delay", width=65, anchor="center")

        self.tree.heading("status", text="Active")
        self.tree.column("status", width=55, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self._edit_selected())
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    def set_events(self, events: list[MacroEvent]):
        self.events = list(events)
        self.refresh()

    def get_events(self) -> list[MacroEvent]:
        return list(self.events)

    def refresh(self):
        """Re-populates treeview rows."""
        self.tree.delete(*self.tree.get_children())
        for idx, ev in enumerate(self.events):
            icon = ev.get_category_icon()
            type_str = f"{icon} {ev.event_type.value.replace('_', ' ').title()}"
            summary = ev.get_summary()
            delay_str = f"{int(ev.delay_after_ms)}ms"
            status_str = "🟢 ON" if ev.enabled else "⚪ OFF"

            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(str(idx + 1), type_str, summary, delay_str, status_str),
            )

    def highlight_step(self, step_idx: int):
        """Highlights the active executing step row."""
        if 0 <= step_idx < len(self.events):
            self.tree.selection_set(str(step_idx))
            self.tree.see(str(step_idx))

    def _on_row_select(self, event):
        sel = self.tree.selection()
        if sel and self.on_step_selected:
            idx = int(sel[0])
            self.on_step_selected(idx)

    def _get_selected_index(self) -> Optional[int]:
        sel = self.tree.selection()
        if sel:
            return int(sel[0])
        return None

    def _edit_selected(self):
        idx = self._get_selected_index()
        if idx is None or idx >= len(self.events):
            return

        ev = self.events[idx]
        t = ev.event_type

        def on_save(updated_ev: MacroEvent):
            self.events[idx] = updated_ev
            self.refresh()
            if self.on_events_modified:
                self.on_events_modified()

        if t in (EventType.MOUSE_CLICK, EventType.MOUSE_MOVE, EventType.MOUSE_DOWN, EventType.MOUSE_UP, EventType.HUMAN_WANDER_ZONE):
            MouseActionDialog(self, ev, on_save)
        elif t == EventType.DELAY:
            DelayActionDialog(self, ev, on_save)
        elif t == EventType.TEXT_TYPE:
            TextTypeActionDialog(self, ev, on_save)

    def _move_up(self):
        idx = self._get_selected_index()
        if idx is not None and idx > 0:
            self.events[idx - 1], self.events[idx] = self.events[idx], self.events[idx - 1]
            self.refresh()
            self.tree.selection_set(str(idx - 1))
            if self.on_events_modified:
                self.on_events_modified()

    def _move_down(self):
        idx = self._get_selected_index()
        if idx is not None and idx < len(self.events) - 1:
            self.events[idx + 1], self.events[idx] = self.events[idx], self.events[idx + 1]
            self.refresh()
            self.tree.selection_set(str(idx + 1))
            if self.on_events_modified:
                self.on_events_modified()

    def _duplicate_selected(self):
        idx = self._get_selected_index()
        if idx is not None:
            import copy
            dup_ev = copy.deepcopy(self.events[idx])
            dup_ev.id = f"{dup_ev.id}_c"
            self.events.insert(idx + 1, dup_ev)
            self.refresh()
            self.tree.selection_set(str(idx + 1))
            if self.on_events_modified:
                self.on_events_modified()

    def _delete_selected(self):
        idx = self._get_selected_index()
        if idx is not None:
            self.events.pop(idx)
            self.refresh()
            if self.on_events_modified:
                self.on_events_modified()

    def _add_action_popup(self):
        """Quick add menu for manual actions."""
        new_ev = MacroEvent(event_type=EventType.MOUSE_CLICK, x=500, y=500, delay_after_ms=100)
        self.events.append(new_ev)
        self.refresh()
        self.tree.selection_set(str(len(self.events) - 1))
        if self.on_events_modified:
            self.on_events_modified()
