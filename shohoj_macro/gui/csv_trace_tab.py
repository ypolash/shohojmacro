"""
CSV Data Trace Tab Frame (v3.0 Enterprise)
Provides real-time spreadsheet tracking, row status highlighting, and live statistics inside Operations Studio.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from shohoj_macro.gui.glass_theme import GlassTheme
from shohoj_macro.core.csv_engine import CSVDataEngine


class CSVTraceTabFrame(ctk.CTkFrame):
    """Embedded live spreadsheet widget for tracking dataset rows in real time."""

    def __init__(self, master, csv_engine: CSVDataEngine, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.csv_engine = csv_engine

        self._setup_styles()
        self._build_ui()

        if self.csv_engine and self.csv_engine.is_loaded:
            self.load_dataset()

        # Wire callback for live updates
        self._old_callback = self.csv_engine.on_status_change
        self.csv_engine.on_status_change = self._on_engine_status_change

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("default")

        style.configure(
            "CSVTrace.Treeview",
            background=GlassTheme.CARD_BG,
            foreground=GlassTheme.TEXT_PRIMARY,
            fieldbackground=GlassTheme.CARD_BG,
            rowheight=28,
            borderwidth=0,
            font=("Inter", 10),
        )

        style.map(
            "CSVTrace.Treeview",
            background=[("selected", GlassTheme.ACCENT_CYAN)],
            foreground=[("selected", "#000000")],
        )

        style.configure(
            "CSVTrace.Treeview.Heading",
            background=GlassTheme.CARD_BG_SECONDARY,
            foreground=GlassTheme.TEXT_MUTED,
            borderwidth=1,
            relief="flat",
            font=("Inter", 10, "bold"),
        )

    def _build_ui(self):
        # Top Toolbar / Stats Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=4, pady=(2, 6))

        # Stats Label
        self.lbl_stats = ctk.CTkLabel(
            top_bar,
            text="Total: 0 | Completed: 0 | Pending: 0",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=GlassTheme.ACCENT_CYAN,
        )
        self.lbl_stats.pack(side="left", padx=4)

        # Controls Container
        ctrls = ctk.CTkFrame(top_bar, fg_color="transparent")
        ctrls.pack(side="right")

        self.opt_filter = ctk.CTkOptionMenu(
            ctrls,
            values=["All Rows", "Pending Only", "Completed Only"],
            width=120,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._apply_filter,
        )
        self.opt_filter.set("All Rows")
        self.opt_filter.pack(side="left", padx=4)

        self.switch_autoscroll = ctk.CTkSwitch(
            ctrls,
            text="Auto-Scroll",
            font=ctk.CTkFont(size=10),
            progress_color=GlassTheme.ACCENT_CYAN,
        )
        self.switch_autoscroll.pack(side="left", padx=4)
        self.switch_autoscroll.select()

        # Treeview Container
        tv_frame = ctk.CTkFrame(self, fg_color="transparent")
        tv_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Scrollbars
        y_scroll = ttk.Scrollbar(tv_frame)
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(tv_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            tv_frame,
            style="CSVTrace.Treeview",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )
        self.tree.pack(fill="both", expand=True)

        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)

        # Configure status highlight tags
        self.tree.tag_configure("status_IN_PROGRESS", background="#3b3b11", foreground="#ffea00")
        self.tree.tag_configure("status_DONE", background="#113b22", foreground="#00ff88")
        self.tree.tag_configure("status_CONFIRMED", background="#113b22", foreground="#00ff88")
        self.tree.tag_configure("status_ERROR", background="#3b1111", foreground="#ff4444")
        self.tree.tag_configure("status_ACTIVE", background="#004d66", foreground="#00ffff")

        # Range scope tags
        self.tree.tag_configure("target_QUEUED", background="#15263a", foreground="#4cc9f0")
        self.tree.tag_configure("out_of_scope", foreground="#6c757d")

        self.target_start_row = None
        self.target_end_row = None
        self.on_set_start_row = None

        # Double-click to copy cell value & Right-click context menu
        self.tree.bind("<Double-1>", self._on_cell_double_click)
        self.tree.bind("<Button-3>", self._on_cell_right_click)

    def _on_cell_double_click(self, event):
        """Copies the double-clicked cell's clean text to the Windows clipboard."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        item_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not item_id or not col_id:
            return

        try:
            col_idx = int(col_id.replace("#", "")) - 1
            vals = self.tree.item(item_id, "values")
            if vals and 0 <= col_idx < len(vals):
                val_to_copy = str(vals[col_idx]).strip()

                # Clean up row markers if first column (e.g. ▶ 31 [START] -> 31)
                if col_idx == 0:
                    import re
                    m = re.search(r"\d+", val_to_copy)
                    if m:
                        val_to_copy = m.group(0)

                # Set to Windows clipboard
                self.clipboard_clear()
                self.clipboard_append(val_to_copy)
                self.update()

                # Flash visual confirmation in vibrant green
                col_name = self.tree["columns"][col_idx] if col_idx < len(self.tree["columns"]) else "Cell"
                self.lbl_stats.configure(
                    text=f"📋 Copied {col_name}: '{val_to_copy}' to clipboard!",
                    text_color="#00ff88"
                )
                self.after(2500, self._recount_stats)
        except Exception:
            pass

    def _on_cell_right_click(self, event):
        """Displays context menu for cell actions."""
        item_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not item_id:
            return

        self.tree.selection_set(item_id)
        col_idx = int(col_id.replace("#", "")) - 1 if col_id else 0
        vals = self.tree.item(item_id, "values")
        if not vals:
            return

        cell_val = str(vals[col_idx]).strip() if 0 <= col_idx < len(vals) else ""
        if col_idx == 0:
            import re
            m = re.search(r"\d+", cell_val)
            if m:
                cell_val = m.group(0)

        try:
            r_num = int(item_id)
        except ValueError:
            r_num = 1

        import tkinter as tk
        menu = tk.Menu(self, tearoff=0, bg="#1a1c23", fg="#ffffff", activebackground="#2A3554", activeforeground="#00ffff")
        label_cell = f"📋 Copy Cell: '{cell_val[:20]}...'" if len(cell_val) > 20 else f"📋 Copy Cell: '{cell_val}'"
        menu.add_command(
            label=label_cell,
            command=lambda: self._copy_text(cell_val)
        )
        menu.add_command(
            label="📄 Copy Entire Row Data",
            command=lambda: self._copy_text("\t".join(str(v) for v in vals))
        )
        menu.add_separator()
        menu.add_command(
            label=f"▶ Set Row {r_num} as Start Row",
            command=lambda: self._set_start_row_action(r_num)
        )
        menu.tk_popup(event.x_root, event.y_root)

    def _copy_text(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self.lbl_stats.configure(
            text=f"📋 Copied to clipboard!",
            text_color="#00ff88"
        )
        self.after(2500, self._recount_stats)

    def _set_start_row_action(self, row_num: int):
        if self.on_set_start_row:
            self.on_set_start_row(row_num)

    def set_target_range(self, start_row: int, end_row: int):
        """Live highlights the active commanded row scope from Operations Studio."""
        self.target_start_row = start_row
        self.target_end_row = end_row
        self._refresh_range_visuals()

    def _refresh_range_visuals(self):
        if not self.csv_engine or not self.csv_engine.is_loaded:
            return

        total = len(self.csv_engine.rows)
        s = self.target_start_row
        e = self.target_end_row

        valid_range = (s is not None and e is not None and s >= 1 and s <= e)
        e_clamped = min(e, total) if valid_range else None

        for item in self.tree.get_children():
            try:
                r_num = int(item)
            except ValueError:
                continue

            vals = list(self.tree.item(item, "values"))
            if not vals:
                continue

            status = str(vals[-1])
            base_tag = self._get_tag_for_status(status)

            # Determine Row column display string and tag
            if valid_range and s <= r_num <= e_clamped:
                if r_num == s and r_num == e_clamped:
                    vals[0] = f"▶ {r_num} [START/END]"
                elif r_num == s:
                    vals[0] = f"▶ {r_num} [START]"
                elif r_num == e_clamped:
                    vals[0] = f"⏹ {r_num} [END]"
                else:
                    vals[0] = f"● {r_num}"

                final_tag = base_tag if base_tag else "target_QUEUED"
            else:
                vals[0] = str(r_num)
                final_tag = base_tag if base_tag else "out_of_scope"

            self.tree.item(item, values=vals, tags=(final_tag,))

        # Update stats counter
        self._recount_stats()

        # Scroll to start row if valid
        if valid_range and self.tree.exists(str(s)):
            try:
                self.tree.see(str(s))
            except Exception:
                pass

    def load_dataset(self):
        """Populates the treeview with loaded CSV/Excel dataset rows."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.csv_engine or not self.csv_engine.is_loaded:
            self.lbl_stats.configure(text="No Dataset Loaded")
            return

        headers = self.csv_engine.headers
        cols = ["Row"] + headers + ["Status"]
        self.tree["columns"] = cols

        self.tree.heading("#0", text="", anchor="w")
        self.tree.column("#0", width=0, stretch=False)

        self.tree.heading("Row", text="Row Scope", anchor="w")
        self.tree.column("Row", width=110, minwidth=85, stretch=False)

        for col in headers:
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=110, minwidth=80)

        self.tree.heading("Status", text="Status Tag", anchor="w")
        self.tree.column("Status", width=120, minwidth=90)

        completed_count = 0

        for r_idx, row in enumerate(self.csv_engine.rows, start=1):
            status = row.get("_macro_status", row.get("Status", "Pending"))
            if status and status.lower() not in ["pending", ""]:
                completed_count += 1

            vals = [str(r_idx)] + [row.get(h, "") for h in headers] + [status]
            tag = self._get_tag_for_status(status)

            self.tree.insert("", "end", iid=str(r_idx), values=vals, tags=(tag,))

        # Apply target range if already configured
        if self.target_start_row is not None and self.target_end_row is not None:
            self._refresh_range_visuals()
        else:
            total = len(self.csv_engine.rows)
            pending = total - completed_count
            self.lbl_stats.configure(
                text=f"Total: {total} | Completed: {completed_count} | Pending: {pending}",
                text_color=GlassTheme.ACCENT_CYAN,
            )

    def _get_tag_for_status(self, status: str) -> str:
        s_upper = str(status).upper()
        if s_upper in ["DONE", "CONFIRMED", "SUCCESS"] or "POLASH" in s_upper:
            return "status_DONE"
        elif "PROGRESS" in s_upper or "FILLING" in s_upper:
            return "status_IN_PROGRESS"
        elif "ERROR" in s_upper or "FAILED" in s_upper:
            return "status_ERROR"
        elif "ACTIVE" in s_upper:
            return "status_ACTIVE"
        return ""

    def update_row_status(self, row_idx: int, status: str):
        """Updates a single row in the treeview live."""
        iid = str(row_idx + 1)
        if self.tree.exists(iid):
            cur_vals = list(self.tree.item(iid, "values"))
            if cur_vals:
                cur_vals[-1] = status
                tag = self._get_tag_for_status(status)
                self.tree.item(iid, values=cur_vals, tags=(tag,))

                if self.switch_autoscroll.get():
                    self.tree.see(iid)
                    self.tree.selection_set(iid)

        # Update stats counter
        self._recount_stats()

    def set_active_row(self, row_idx: int):
        """Highlights the currently processing working row."""
        iid = str(row_idx + 1)
        if self.tree.exists(iid):
            vals = list(self.tree.item(iid, "values"))
            if vals:
                vals[0] = f"⚡ {row_idx + 1} [ACTIVE]"
                self.tree.item(iid, values=vals, tags=("status_ACTIVE",))
            self.tree.selection_set(iid)
            if self.switch_autoscroll.get():
                self.tree.see(iid)

    def _recount_stats(self):
        if not self.csv_engine or not self.csv_engine.is_loaded:
            return
        total = len(self.csv_engine.rows)
        completed = 0
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            if vals and len(vals) > 0:
                st = str(vals[-1]).lower()
                if st and st not in ["pending", ""]:
                    completed += 1
        pending = total - completed

        s = self.target_start_row
        e = self.target_end_row
        if s is not None and e is not None and 1 <= s <= total and s <= e:
            e_clamped = min(e, total)
            scoped_count = max(0, e_clamped - s + 1)
            scope_str = f"🎯 Scope: Rows {s} → {e_clamped} ({scoped_count} queued) | "
        else:
            scope_str = ""

        self.lbl_stats.configure(
            text=f"{scope_str}Total: {total} | Completed: {completed} | Pending: {pending}",
            text_color=GlassTheme.ACCENT_CYAN,
        )

    def _apply_filter(self, choice: str):
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            if not vals:
                continue
            st = str(vals[-1]).lower()
            is_completed = st and st not in ["pending", ""]

            if choice == "All Rows":
                self.tree.reattach(item, "", "end")
            elif choice == "Pending Only":
                if not is_completed:
                    self.tree.reattach(item, "", "end")
                else:
                    self.tree.detach(item)
            elif choice == "Completed Only":
                if is_completed:
                    self.tree.reattach(item, "", "end")
                else:
                    self.tree.detach(item)

    def _on_engine_status_change(self, row_idx: int, status: str):
        self.after(0, lambda: self.update_row_status(row_idx, status))
        if self._old_callback:
            self._old_callback(row_idx, status)
