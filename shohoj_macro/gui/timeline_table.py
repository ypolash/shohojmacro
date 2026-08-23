"""
Interactive Visual Timeline & Step-by-Step Action Table Editor
Provides multi-selection, bulk operations, right-click context menu, search filter and tooltips.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import customtkinter as ctk
from typing import Callable, Optional
from shohoj_macro.core.events import MacroEvent, EventType
from shohoj_macro.gui.glass_theme import GlassTheme, GlassCard, GlassButton, GlassTooltip
from shohoj_macro.gui.action_dialogs import MouseActionDialog, DelayActionDialog, TextTypeActionDialog


class TimelineTableEditor(GlassCard):
    """Visual table editor with multi-selection and bulk operations."""

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
        self._filter_query = ""

        self._build_toolbar()
        self._build_table()
        self._build_context_menu()

    def _build_toolbar(self):
        # 1. Top Title & Search Bar
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            self.top_bar,
            text="⚡ Action Sequence Timeline",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=13, weight="bold"),
            text_color=GlassTheme.TEXT_PRIMARY,
        ).pack(side="left")

        # Search / Filter Bar
        self.search_entry = ctk.CTkEntry(
            self.top_bar,
            placeholder_text="🔍 Filter actions...",
            width=170,
            height=26,
            corner_radius=8,
            fg_color=GlassTheme.BG_DARK,
            border_color=GlassTheme.CARD_BORDER,
            font=ctk.CTkFont(size=11),
        )
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_filter_changed())

        # 2. Action Buttons Toolbar
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.pack(fill="x", padx=12, pady=(0, 6))

        # Labeled Action Buttons
        self.btn_add = ctk.CTkButton(
            self.toolbar,
            text="➕ Add Action",
            width=86,
            height=26,
            corner_radius=6,
            fg_color="#182A3A",
            hover_color=GlassTheme.ACCENT_BLUE,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
            command=self._add_action_popup,
        )
        self.btn_add.pack(side="left", padx=(0, 4))
        GlassTooltip(self.btn_add, "Add a new mouse or keyboard action step")

        self.btn_edit = ctk.CTkButton(
            self.toolbar,
            text="✏️ Edit",
            width=58,
            height=26,
            corner_radius=6,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color=GlassTheme.ACCENT_CYAN,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
            command=self._edit_selected,
        )
        self.btn_edit.pack(side="left", padx=2)
        GlassTooltip(self.btn_edit, "Edit parameters of selected action (Double-click)")

        self.btn_dup = ctk.CTkButton(
            self.toolbar,
            text="📋 Duplicate",
            width=80,
            height=26,
            corner_radius=6,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
            command=self._duplicate_selected,
        )
        self.btn_dup.pack(side="left", padx=2)
        GlassTooltip(self.btn_dup, "Duplicate selected action(s) (Ctrl+D)")

        self.btn_toggle = ctk.CTkButton(
            self.toolbar,
            text="👁️ Toggle",
            width=70,
            height=26,
            corner_radius=6,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
            command=self._toggle_selected,
        )
        self.btn_toggle.pack(side="left", padx=2)
        GlassTooltip(self.btn_toggle, "Enable or disable selected action(s)")

        self.btn_del = ctk.CTkButton(
            self.toolbar,
            text="🗑️ Delete",
            width=68,
            height=26,
            corner_radius=6,
            fg_color="#3A181C",
            hover_color=GlassTheme.ACCENT_RED,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
            command=self._delete_selected,
        )
        self.btn_del.pack(side="left", padx=2)
        GlassTooltip(self.btn_del, "Delete selected action(s) (Delete key)")

        # Right side: Move Up / Down / Clear All
        self.btn_clear = ctk.CTkButton(
            self.toolbar,
            text="🧹 Clear All",
            width=74,
            height=26,
            corner_radius=6,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color=GlassTheme.ACCENT_RED,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=10),
            command=self._clear_all,
        )
        self.btn_clear.pack(side="right", padx=(4, 0))
        GlassTooltip(self.btn_clear, "Remove all actions from the timeline")

        self.btn_down = ctk.CTkButton(
            self.toolbar,
            text="▼ Down",
            width=58,
            height=26,
            corner_radius=6,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=10, weight="bold"),
            command=self._move_down,
        )
        self.btn_down.pack(side="right", padx=2)
        GlassTooltip(self.btn_down, "Move selected action down")

        self.btn_up = ctk.CTkButton(
            self.toolbar,
            text="▲ Up",
            width=50,
            height=26,
            corner_radius=6,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=10, weight="bold"),
            command=self._move_up,
        )
        self.btn_up.pack(side="right", padx=2)
        GlassTooltip(self.btn_up, "Move selected action up")

    def _build_table(self):
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
        # Extended selection mode enables Shift+Click and Ctrl+Click multi-selection
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")

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

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bindings
        self.tree.bind("<Double-1>", lambda e: self._edit_selected())
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)
        self.tree.bind("<Delete>", lambda e: self._delete_selected())
        self.tree.bind("<Control-a>", lambda e: self._select_all())
        self.tree.bind("<Control-d>", lambda e: self._duplicate_selected())
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _build_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0, bg="#161928", fg="#FFFFFF", activebackground="#00F0FF", activeforeground="#000000", bd=1)
        self.context_menu.add_command(label="✏️ Edit Action...", command=self._edit_selected)
        self.context_menu.add_command(label="📋 Duplicate (Ctrl+D)", command=self._duplicate_selected)
        self.context_menu.add_command(label="👁️ Toggle Enable / Disable", command=self._toggle_selected)
        self.context_menu.add_command(label="⏱️ Adjust Delay...", command=self._batch_adjust_delay)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="▲ Move Up", command=self._move_up)
        self.context_menu.add_command(label="▼ Move Down", command=self._move_down)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Delete Selected (Del)", command=self._delete_selected)
        self.context_menu.add_command(label="🧹 Clear All Actions", command=self._clear_all)

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def set_events(self, events: list[MacroEvent]):
        self.events = list(events)
        self.refresh()

    def get_events(self) -> list[MacroEvent]:
        return list(self.events)

    def append_event_live(self, ev: MacroEvent):
        """Appends a new event live during recording without full re-render."""
        idx = len(self.events)
        self.events.append(ev)
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
        self.tree.see(str(idx))

    def refresh(self):
        """Re-populates treeview rows based on current events and filter query."""
        self.tree.delete(*self.tree.get_children())
        query = self._filter_query.lower()

        for idx, ev in enumerate(self.events):
            summary = ev.get_summary()
            type_name = ev.event_type.value
            if query and (query not in summary.lower() and query not in type_name.lower()):
                continue

            icon = ev.get_category_icon()
            type_str = f"{icon} {type_name.replace('_', ' ').title()}"
            delay_str = f"{int(ev.delay_after_ms)}ms"
            status_str = "🟢 ON" if ev.enabled else "⚪ OFF"

            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(str(idx + 1), type_str, summary, delay_str, status_str),
            )

    def _on_filter_changed(self):
        self._filter_query = self.search_entry.get().strip()
        self.refresh()

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

    def _get_selected_indices(self) -> list[int]:
        sel = self.tree.selection()
        if sel:
            return sorted([int(i) for i in sel])
        return []

    def _select_all(self):
        all_items = self.tree.get_children()
        self.tree.selection_set(all_items)
        return "break"

    def _edit_selected(self):
        indices = self._get_selected_indices()
        if not indices:
            return
        idx = indices[0]
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

    def _duplicate_selected(self):
        indices = self._get_selected_indices()
        if not indices:
            return
        import copy
        new_indices = []
        offset = 0
        for idx in indices:
            actual_idx = idx + offset
            dup_ev = copy.deepcopy(self.events[actual_idx])
            dup_ev.id = f"{dup_ev.id}_c"
            self.events.insert(actual_idx + 1, dup_ev)
            new_indices.append(actual_idx + 1)
            offset += 1

        self.refresh()
        self.tree.selection_set([str(i) for i in new_indices])
        if self.on_events_modified:
            self.on_events_modified()

    def _toggle_selected(self):
        indices = self._get_selected_indices()
        if not indices:
            return
        for idx in indices:
            if 0 <= idx < len(self.events):
                self.events[idx].enabled = not self.events[idx].enabled
        self.refresh()
        self.tree.selection_set([str(i) for i in indices])
        if self.on_events_modified:
            self.on_events_modified()

    def _delete_selected(self):
        indices = self._get_selected_indices()
        if not indices:
            return

        for idx in reversed(indices):
            if 0 <= idx < len(self.events):
                self.events.pop(idx)

        self.refresh()
        if self.on_events_modified:
            self.on_events_modified()

    def _clear_all(self):
        if not self.events:
            return
        if messagebox.askyesno("Clear All", "Are you sure you want to remove all actions from the timeline?"):
            self.events.clear()
            self.refresh()
            if self.on_events_modified:
                self.on_events_modified()

    def _batch_adjust_delay(self):
        indices = self._get_selected_indices()
        if not indices:
            return
        val = simpledialog.askinteger("Adjust Delay", "Set delay (ms) for all selected actions:", parent=self, minvalue=0, maxvalue=60000)
        if val is not None:
            for idx in indices:
                if 0 <= idx < len(self.events):
                    self.events[idx].delay_after_ms = float(val)
            self.refresh()
            self.tree.selection_set([str(i) for i in indices])
            if self.on_events_modified:
                self.on_events_modified()

    def _move_up(self):
        indices = self._get_selected_indices()
        if not indices or indices[0] == 0:
            return
        for idx in indices:
            self.events[idx - 1], self.events[idx] = self.events[idx], self.events[idx - 1]
        self.refresh()
        self.tree.selection_set([str(i - 1) for i in indices])
        if self.on_events_modified:
            self.on_events_modified()

    def _move_down(self):
        indices = self._get_selected_indices()
        if not indices or indices[-1] >= len(self.events) - 1:
            return
        for idx in reversed(indices):
            self.events[idx + 1], self.events[idx] = self.events[idx], self.events[idx + 1]
        self.refresh()
        self.tree.selection_set([str(i + 1) for i in indices])
        if self.on_events_modified:
            self.on_events_modified()

    def _add_action_popup(self):
        new_ev = MacroEvent(event_type=EventType.MOUSE_CLICK, x=500, y=500, delay_after_ms=100)
        self.events.append(new_ev)
        self.refresh()
        self.tree.selection_set(str(len(self.events) - 1))
        if self.on_events_modified:
            self.on_events_modified()
