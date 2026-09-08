import os
from tkinter import filedialog, messagebox
import customtkinter as ctk
from shohoj_macro.gui.glass_theme import GlassTheme, GlassButton
from shohoj_macro.ai.orchestrator import OperationOrchestrator
from shohoj_macro.core.settings_manager import SettingsManager


class OperationStudioPanel(ctk.CTkFrame):
    """
    Control sidebar panel for configuring and launching operations.
    Supports semi-automated form-filling, custom confirmation words, and completion actions.
    """

    def __init__(self, master, orchestrator: OperationOrchestrator, log_panel, show_settings_callback=None, on_switch_to_builder=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.orchestrator = orchestrator
        self.log_panel = log_panel
        self.show_settings_callback = show_settings_callback
        self.on_switch_to_builder = on_switch_to_builder
        self.orchestrator.on_log = self._on_log
        self.orchestrator.on_supervised_intercept = self._show_intercept_popup
        self.selected_macro_path = ""

        lbl = ctk.CTkLabel(self, text="🚀 AI Operation Studio", font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(pady=(8, 2))

        # Status Badge (IDLE / RUNNING / WAITING_MANUAL / STOPPED)
        self.status_badge = ctk.CTkLabel(
            self,
            text="● IDLE",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#181B28",
            text_color=GlassTheme.TEXT_MUTED,
            corner_radius=8,
            padx=10,
            pady=3,
        )
        self.status_badge.pack(fill="x", padx=10, pady=(2, 6))

        # 1. Target URL
        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.pack(fill="x", padx=10, pady=(4, 4))
        ctk.CTkLabel(url_frame, text="Target URL (Optional):", text_color=GlassTheme.TEXT_SECONDARY, font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.entry_url = ctk.CTkEntry(url_frame, placeholder_text="https://... (Leave blank to use active window)")
        self.entry_url.pack(fill="x", pady=(2, 0))

        # 2. Row Range
        range_frame = ctk.CTkFrame(self, fg_color="transparent")
        range_frame.pack(fill="x", padx=10, pady=(4, 4))

        start_frame = ctk.CTkFrame(range_frame, fg_color="transparent")
        start_frame.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(start_frame, text="Start Row", text_color=GlassTheme.TEXT_SECONDARY, font=ctk.CTkFont(size=11)).pack(anchor="w")

        start_input_row = ctk.CTkFrame(start_frame, fg_color="transparent")
        start_input_row.pack(fill="x", pady=(2, 0))

        self.btn_prev_row = ctk.CTkButton(
            start_input_row,
            text="❮",
            width=24,
            height=28,
            command=self._step_prev_row,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#2A3554",
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=4,
        )
        self.btn_prev_row.pack(side="left", padx=(0, 2))

        self.entry_start_row = ctk.CTkEntry(start_input_row, width=45)
        self.entry_start_row.pack(side="left", fill="x", expand=True)
        self.entry_start_row.insert(0, "1")

        self.btn_next_row = ctk.CTkButton(
            start_input_row,
            text="❯ Next",
            width=58,
            height=28,
            command=self._step_next_row,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#2A3554",
            text_color=GlassTheme.ACCENT_CYAN,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=4,
        )
        self.btn_next_row.pack(side="left", padx=(2, 0))

        end_frame = ctk.CTkFrame(range_frame, fg_color="transparent")
        end_frame.pack(side="right", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(end_frame, text="End Row", text_color=GlassTheme.TEXT_SECONDARY, font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.entry_end_row = ctk.CTkEntry(end_frame, width=60)
        self.entry_end_row.pack(fill="x", pady=(2, 0))
        self.entry_end_row.insert(0, "9999")

        self.on_range_changed = None
        self.entry_start_row.bind("<KeyRelease>", self._on_range_entry_changed)
        self.entry_end_row.bind("<KeyRelease>", self._on_range_entry_changed)
        self.entry_start_row.bind("<FocusOut>", self._on_range_entry_changed)
        self.entry_end_row.bind("<FocusOut>", self._on_range_entry_changed)

        # 3. Macro Selector & Quick Record
        macro_frame = ctk.CTkFrame(self, fg_color="transparent")
        macro_frame.pack(fill="x", padx=10, pady=(4, 4))
        ctk.CTkLabel(macro_frame, text="Macro Template (.shj):", text_color=GlassTheme.TEXT_SECONDARY, font=ctk.CTkFont(size=11)).pack(anchor="w")

        macro_btn_row = ctk.CTkFrame(macro_frame, fg_color="transparent")
        macro_btn_row.pack(fill="x", pady=(2, 0))

        self.btn_load_macro = ctk.CTkButton(
            macro_btn_row,
            text="📁 Select (.shj)",
            command=self._load_macro,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#263352",
            height=28,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.btn_load_macro.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.btn_record_new = ctk.CTkButton(
            macro_btn_row,
            text="● Record Macro",
            command=self._switch_to_builder,
            fg_color="#7A1C24",
            hover_color="#A82834",
            text_color="#FFFFFF",
            height=28,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.btn_record_new.pack(side="right", fill="x", expand=True, padx=(2, 0))

        # Macro Label & Clear Row
        self.macro_info_row = ctk.CTkFrame(macro_frame, fg_color="transparent")
        self.macro_info_row.pack(fill="x", pady=(3, 0))

        self.lbl_macro = ctk.CTkLabel(
            self.macro_info_row,
            text="No Macro Loaded",
            text_color=GlassTheme.TEXT_MUTED,
            font=ctk.CTkFont(size=10)
        )
        self.lbl_macro.pack(side="left", anchor="w")

        self.btn_clear_macro = ctk.CTkButton(
            self.macro_info_row,
            text="✖ Clear",
            width=50,
            height=20,
            command=self._clear_macro,
            fg_color="#3A181C",
            hover_color=GlassTheme.ACCENT_RED,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=9, weight="bold"),
            corner_radius=6,
        )

        # 4. Confirmation Tag & Row Completion Action
        tag_frame = ctk.CTkFrame(self, fg_color="transparent")
        tag_frame.pack(fill="x", padx=10, pady=(4, 4))

        ctk.CTkLabel(tag_frame, text="Confirmation Word:", text_color=GlassTheme.TEXT_SECONDARY, font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.entry_confirmation_word = ctk.CTkEntry(tag_frame, placeholder_text="e.g. Polash")
        self.entry_confirmation_word.pack(fill="x", pady=(2, 4))
        self.entry_confirmation_word.insert(0, "Polash")

        ctk.CTkLabel(tag_frame, text="After Row Completion:", text_color=GlassTheme.TEXT_SECONDARY, font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.opt_completion_action = ctk.CTkOptionMenu(
            tag_frame,
            values=["➡️ Move to Next Row", "🔄 Repeat Same Row", "⏸️ Pause Before Next Row"],
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            button_color="#2A3554",
        )
        self.opt_completion_action.set("➡️ Move to Next Row")
        self.opt_completion_action.pack(fill="x", pady=(2, 0))

        # 5. Switches (Semi-Automated Form Fill & Auto Profile Launch)
        switch_frame = ctk.CTkFrame(self, fg_color="transparent")
        switch_frame.pack(fill="x", padx=10, pady=(6, 4))

        self.switch_semi_automated = ctk.CTkSwitch(
            switch_frame,
            text="Semi-Automated (Pause for QR/Check)",
            font=ctk.CTkFont(size=11, weight="bold"),
            progress_color=GlassTheme.ACCENT_CYAN,
        )
        self.switch_semi_automated.pack(anchor="w", pady=(2, 4))
        self.switch_semi_automated.select()  # Enabled by default

        self.switch_auto_profile = ctk.CTkSwitch(
            switch_frame,
            text="Auto-Launch NST Profiles",
            font=ctk.CTkFont(size=11),
            progress_color=GlassTheme.ACCENT_BLUE,
        )
        self.switch_auto_profile.pack(anchor="w", pady=(2, 4))

        # 6. Action Control Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(8, 10))

        self.btn_resume = ctk.CTkButton(
            btn_frame,
            text="✅ Mark Done & Next (F9)",
            command=self.resume_done_op,
            fg_color="#143A22",
            hover_color=GlassTheme.ACCENT_EMERALD,
            text_color=GlassTheme.ACCENT_EMERALD,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.btn_resume.pack(fill="x", pady=(0, 6))

        self.btn_start = ctk.CTkButton(
            btn_frame,
            text="🚀 Start Bulk Execution",
            command=self.start_op,
            fg_color=GlassTheme.ACCENT_CYAN,
            hover_color="#00B4D8",
            text_color="#000000",
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.btn_start.pack(fill="x", pady=(0, 6))

        row_btns = ctk.CTkFrame(btn_frame, fg_color="transparent")
        row_btns.pack(fill="x")

        self.btn_test = ctk.CTkButton(
            row_btns,
            text="⚡ Trial (1 Row)",
            command=self.test_run_op,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#2E3A59",
            text_color=GlassTheme.TEXT_PRIMARY,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.btn_test.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_stop = ctk.CTkButton(
            row_btns,
            text="⏹ Stop",
            command=self.stop_op,
            fg_color="#3A181C",
            hover_color=GlassTheme.ACCENT_RED,
            text_color=GlassTheme.ACCENT_RED,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(3, 0))

        # Restore saved state
        state = SettingsManager().config.get("state", {})
        if state.get("last_target_url"):
            self.entry_url.insert(0, state["last_target_url"])
        if state.get("last_macro_path") and os.path.exists(state["last_macro_path"]):
            self.selected_macro_path = state["last_macro_path"]
            self.lbl_macro.configure(text=f"Selected: {os.path.basename(self.selected_macro_path)}", text_color=GlassTheme.ACCENT_CYAN)
            self.btn_clear_macro.pack(side="right")

        self.entry_url.bind("<KeyRelease>", self._save_url_state)
        self.orchestrator.on_execution_state_change = self.set_execution_state

    def _clear_macro(self):
        self.selected_macro_path = ""
        self.lbl_macro.configure(text="No Macro Loaded", text_color=GlassTheme.TEXT_MUTED)
        self.btn_clear_macro.pack_forget()
        SettingsManager().config.setdefault("state", {})["last_macro_path"] = ""
        SettingsManager().save()
        if self.log_panel:
            self.log_panel.log("Deselected / Cleared Macro Template.", "INFO")

    def on_csv_loaded(self, filepath: str):
        if not filepath:
            return
        filename = os.path.basename(filepath)
        sm = SettingsManager()
        saved_row = sm.config.get("csv_states", {}).get(filename)
        if saved_row:
            self.entry_start_row.delete(0, "end")
            self.entry_start_row.insert(0, str(saved_row))
            if hasattr(self, 'log_panel') and self.log_panel:
                self.log_panel.log(f"Smart Memory: Set start row to {saved_row} for '{filename}'", "INFO")

    def _save_url_state(self, event=None):
        SettingsManager().config.setdefault("state", {})["last_target_url"] = self.entry_url.get().strip()
        SettingsManager().save()

    def _load_macro(self):
        path = filedialog.askopenfilename(filetypes=[("Shohoj Macro Files", "*.shj")])
        if path:
            self.selected_macro_path = path
            name = os.path.basename(path)
            self.lbl_macro.configure(text=f"Selected: {name}", text_color=GlassTheme.ACCENT_CYAN)
            self.btn_clear_macro.pack(side="right")
            if self.log_panel:
                self.log_panel.log(f"Loaded Macro for Operation: {name}", "INFO")
            SettingsManager().config.setdefault("state", {})["last_macro_path"] = path
            SettingsManager().save()

    def _switch_to_builder(self):
        if self.on_switch_to_builder:
            self.on_switch_to_builder()
        else:
            cur = self.master
            while cur:
                if hasattr(cur, '_switch_mode'):
                    cur._switch_mode("builder")
                    break
                cur = getattr(cur, 'master', None)

    def set_execution_state(self, state: str, curr_row: int = 0, end_row: int = 0):
        """Thread-safe state machine updates for buttons and status badge."""
        def _update():
            if state == "RUNNING":
                total_str = f" of {end_row}" if end_row > 0 else ""
                self.status_badge.configure(
                    text=f"🟢 RUNNING - Row {curr_row}{total_str}",
                    fg_color="#123B22",
                    text_color=GlassTheme.ACCENT_EMERALD
                )
                self.btn_start.configure(
                    text=f"⏳ Running Row {curr_row}{total_str}...",
                    state="disabled",
                    fg_color="#1A2D40",
                    text_color="#64B5F6"
                )
                self.btn_stop.configure(
                    text="⏹ STOP OPERATION",
                    state="normal",
                    fg_color=GlassTheme.ACCENT_RED,
                    text_color="#FFFFFF"
                )
                self.btn_test.configure(state="disabled")
                self.btn_resume.configure(state="disabled", fg_color="#143A22", text_color=GlassTheme.TEXT_MUTED)
            elif state == "WAITING_MANUAL":
                self.status_badge.configure(
                    text=f"🔔 WAITING FOR YOU - Row {curr_row}",
                    fg_color="#3A2810",
                    text_color="#FFB300"
                )
                self.btn_start.configure(
                    text="⏸️ Paused (Awaiting Your Input)",
                    state="disabled"
                )
                self.btn_stop.configure(
                    text="⏹ STOP OPERATION",
                    state="normal",
                    fg_color=GlassTheme.ACCENT_RED,
                    text_color="#FFFFFF"
                )
                self.btn_resume.configure(
                    text="👉 CLICK: Mark Done & Next (F9)",
                    state="normal",
                    fg_color=GlassTheme.ACCENT_EMERALD,
                    text_color="#000000"
                )
            elif state == "STOPPED":
                self.status_badge.configure(
                    text="⏹ STOPPED",
                    fg_color="#3A181C",
                    text_color=GlassTheme.ACCENT_RED
                )
                self.btn_start.configure(
                    text="🚀 Start Bulk Execution",
                    state="normal",
                    fg_color=GlassTheme.ACCENT_CYAN,
                    text_color="#000000"
                )
                self.btn_stop.configure(
                    text="⏹ Stop",
                    state="normal",
                    fg_color="#3A181C",
                    text_color=GlassTheme.TEXT_MUTED
                )
                self.btn_test.configure(state="normal")
                self.btn_resume.configure(
                    text="✅ Mark Done & Next (F9)",
                    state="normal",
                    fg_color="#143A22",
                    text_color=GlassTheme.ACCENT_EMERALD
                )
            elif state == "FINISHED":
                self.status_badge.configure(
                    text="🎉 COMPLETED ALL ROWS",
                    fg_color="#143A22",
                    text_color=GlassTheme.ACCENT_EMERALD
                )
                self.btn_start.configure(
                    text="🚀 Start Bulk Execution",
                    state="normal",
                    fg_color=GlassTheme.ACCENT_CYAN,
                    text_color="#000000"
                )
                self.btn_stop.configure(
                    text="⏹ Stop",
                    state="normal",
                    fg_color="#3A181C",
                    text_color=GlassTheme.TEXT_MUTED
                )
                self.btn_test.configure(state="normal")
                self.btn_resume.configure(
                    text="✅ Mark Done & Next (F9)",
                    state="normal",
                    fg_color="#143A22",
                    text_color=GlassTheme.ACCENT_EMERALD
                )
            else:  # IDLE
                self.status_badge.configure(
                    text="● IDLE",
                    fg_color="#181B28",
                    text_color=GlassTheme.TEXT_MUTED
                )
                self.btn_start.configure(
                    text="🚀 Start Bulk Execution",
                    state="normal",
                    fg_color=GlassTheme.ACCENT_CYAN,
                    text_color="#000000"
                )
                self.btn_stop.configure(
                    text="⏹ Stop",
                    state="normal",
                    fg_color="#3A181C",
                    text_color=GlassTheme.TEXT_MUTED
                )
                self.btn_test.configure(state="normal")
                self.btn_resume.configure(
                    text="✅ Mark Done & Next (F9)",
                    state="normal",
                    fg_color="#143A22",
                    text_color=GlassTheme.ACCENT_EMERALD
                )

        self.after(0, _update)

    def _on_range_entry_changed(self, event=None):
        if self.on_range_changed:
            try:
                s_str = self.entry_start_row.get().strip()
                e_str = self.entry_end_row.get().strip()
                if s_str and e_str:
                    s = int(s_str)
                    e = int(e_str)
                    self.on_range_changed(s, e)
            except Exception:
                pass

    def _step_next_row(self):
        """Advances to next row (or resumes in WAITING_MANUAL)."""
        if hasattr(self.orchestrator, 'is_waiting_manual_step') and self.orchestrator.is_waiting_manual_step():
            self.resume_done_op()
            return

        try:
            cur = int(self.entry_start_row.get().strip() or "1")
            total = self.orchestrator.excel.get_row_count() if self.orchestrator and self.orchestrator.excel else 9999
            next_row = min(total, cur + 1)
            self.entry_start_row.delete(0, "end")
            self.entry_start_row.insert(0, str(next_row))
            self._on_range_entry_changed()
            if self.log_panel:
                self.log_panel.log(f"Moved to Row {next_row}", "INFO")
        except Exception:
            pass

    def _step_prev_row(self):
        try:
            cur = int(self.entry_start_row.get().strip() or "1")
            prev_row = max(1, cur - 1)
            self.entry_start_row.delete(0, "end")
            self.entry_start_row.insert(0, str(prev_row))
            self._on_range_entry_changed()
            if self.log_panel:
                self.log_panel.log(f"Moved back to Row {prev_row}", "INFO")
        except Exception:
            pass

    def on_csv_loaded(self, filepath: str = None):
        """Called when a new CSV dataset is loaded into the engine."""
        row_count = self.orchestrator.excel.get_row_count() if self.orchestrator and self.orchestrator.excel else 0
        if row_count > 0:
            start_row = 1
            if filepath:
                import os
                from shohoj_macro.core.settings_manager import SettingsManager
                csv_name = os.path.basename(filepath)
                sm = SettingsManager()
                saved_row = sm.config.get("csv_states", {}).get(csv_name)
                if saved_row and isinstance(saved_row, int) and 1 <= saved_row <= row_count:
                    start_row = saved_row

            self.entry_start_row.delete(0, "end")
            self.entry_start_row.insert(0, str(start_row))

            self.entry_end_row.delete(0, "end")
            self.entry_end_row.insert(0, str(row_count))

            self._on_range_entry_changed()

    def _get_op_params(self):
        try:
            start = int(self.entry_start_row.get() or "1")
        except Exception:
            start = 1
        try:
            end = int(self.entry_end_row.get() or "9999")
        except Exception:
            end = 9999
        url = self.entry_url.get().strip()
        return start, end, url

    def test_run_op(self):
        if not self.selected_macro_path:
            messagebox.showwarning("No Macro", "Please select a .shj macro template first.")
            return
        start, end, url = self._get_op_params()
        if not url and self.log_panel:
            self.log_panel.log("No Target URL provided. Operating on active window.", "INFO")

        conf_word = self.entry_confirmation_word.get().strip() or "Polash"
        action = self.opt_completion_action.get()
        semi_auto = bool(self.switch_semi_automated.get())

        if self.log_panel:
            self.log_panel.log("Starting SUPERVISED TRIAL RUN...", "WARNING")

        self.set_execution_state("RUNNING", start, start)

        self.orchestrator.execute_operation(
            start_row=start,
            end_row=start,
            macro_path=self.selected_macro_path,
            target_url=url,
            test_run=True,
            supervised=True,
            auto_launch_profiles=bool(self.switch_auto_profile.get()),
            semi_automated=semi_auto,
            confirmation_word=conf_word,
            completion_action=action,
        )

    def start_op(self):
        if not self.selected_macro_path:
            messagebox.showwarning("No Macro", "Please select a .shj macro template first.")
            return
        start, end, url = self._get_op_params()
        if not url and self.log_panel:
            self.log_panel.log("No Target URL provided. Operating on active window.", "INFO")

        conf_word = self.entry_confirmation_word.get().strip() or "Polash"
        action = self.opt_completion_action.get()
        semi_auto = bool(self.switch_semi_automated.get())

        if self.log_panel:
            self.log_panel.log(f"Starting Bulk Execution (Semi-Auto: {semi_auto}, Word: '{conf_word}')...", "SUCCESS")

        self.set_execution_state("RUNNING", start, end)

        self.orchestrator.execute_operation(
            start_row=start,
            end_row=end,
            macro_path=self.selected_macro_path,
            target_url=url,
            test_run=False,
            supervised=False,
            auto_launch_profiles=bool(self.switch_auto_profile.get()),
            semi_automated=semi_auto,
            confirmation_word=conf_word,
            completion_action=action,
        )

    def resume_done_op(self):
        conf_word = self.entry_confirmation_word.get().strip() or "Polash"
        action = self.opt_completion_action.get()

        if hasattr(self.orchestrator, 'resume_manual_step'):
            self.orchestrator.resume_manual_step(conf_word=conf_word, action=action)
        elif hasattr(self.orchestrator.player, 'resume'):
            self.orchestrator.player.resume()

        if self.log_panel:
            self.log_panel.log(f"Marked Row Complete ('{conf_word}'). Resuming...", "SUCCESS")

    def stop_op(self):
        self.orchestrator.stop()
        self.set_execution_state("STOPPED")
        if self.log_panel:
            self.log_panel.log("Stopping Operation...", "WARNING")

    def _on_log(self, msg: str):
        if self.log_panel:
            self.after(0, lambda: self.log_panel.log(msg, "INFO"))

    def _show_intercept_popup(self, event, resume_callback):
        def popup_logic():
            self.orchestrator.cdp.highlight_element(event.selector)
            ans = messagebox.askyesno(
                "Supervised Action",
                f"Ready to execute action on:\n{event.selector}\n\nIs the red-highlighted element correct?"
            )
            self.orchestrator.cdp.clear_highlights()
            resume_callback(ans)

        self.after(0, popup_logic)
