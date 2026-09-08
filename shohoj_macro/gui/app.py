"""
Shohoj Macro Studio - Main Application Window (v2.0.0 Enterprise Edition)
Developed by Polash Khan (ypolash2)
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import winsound
from datetime import datetime

from shohoj_macro.gui.glass_theme import GlassTheme, GlassCard, GlassButton, GlassTooltip
from shohoj_macro.gui.timeline_table import TimelineTableEditor
from shohoj_macro.gui.trajectory_canvas import TrajectoryCanvas
from shohoj_macro.gui.playback_log import PlaybackLogPanel
from shohoj_macro.gui.dynamic_island import DynamicIslandHUD
from shohoj_macro.gui.macro_library import MacroLibrarySidebar
from shohoj_macro.gui.browser_panel import BrowserCompanionPanel
from shohoj_macro.gui.csv_dock import CSVDockPanel
from shohoj_macro.gui.image_snipper import ScreenSnipperModal
from shohoj_macro.gui.settings_dialog import SettingsDialog
from shohoj_macro.gui.export_dialog import ExportDialog
from shohoj_macro.gui.about_dialog import AboutDialog
from shohoj_macro.gui.operation_panel import OperationStudioPanel
from shohoj_macro.gui.ai_training_wizard import AITrainingWizard
from shohoj_macro.gui.csv_trace_tab import CSVTraceTabFrame

from shohoj_macro.core.events import MacroEvent, EventType
from shohoj_macro.core.recorder import MacroRecorder
from shohoj_macro.core.player import MacroPlayer, PlaybackState
from shohoj_macro.core.storage import MacroStorage
from shohoj_macro.core.exporter import MacroExporter
from shohoj_macro.core.hotkeys import GlobalHotkeyManager
from shohoj_macro.core.browser_bridge import BrowserBridgeServer
from shohoj_macro.utils.dpi_helper import init_dpi_awareness
from shohoj_macro.utils.window_effects import apply_mica
from shohoj_macro.version import __app_name__, __version__, __author__, __username__


class ShohojMacroStudio(ctk.CTk):
    """Master Application Window."""

    def __init__(self):
        super().__init__()
        init_dpi_awareness()
        GlassTheme.apply_global_settings()

        self.title(f"{__app_name__} v{__version__} • Enterprise Studio")
        self.geometry("1260x780")
        self.minsize(1080, 680)
        self.configure(fg_color=GlassTheme.BG_DARK) # CTk root cannot be transparent
        # Apply Windows 11 Mica Blur
        self.after(10, lambda: apply_mica(self.winfo_id(), dark_mode=True))

        # Core Engines
        self.recorder = MacroRecorder(on_event_recorded=self._on_event_recorded)
        self.player = MacroPlayer(
            on_step_started=self._on_step_started,
            on_loop_completed=self._on_loop_completed,
            on_playback_finished=self._on_playback_finished,
            on_log_message=self._on_log_message,
        )
        self.hotkeys = GlobalHotkeyManager(
            on_toggle_record=self._hotkey_toggle_record,
            on_toggle_play=self._hotkey_toggle_play,
            on_emergency_stop=self._hotkey_stop,
        )
        self.browser_bridge = BrowserBridgeServer()
        self.browser_bridge.on_element_picked = self._on_browser_element_picked
        self.browser_bridge.on_status_change = self._on_browser_status_change

        # v3.0 Orchestrator Engines
        from shohoj_macro.core.proxy_manager import ProxySessionManager
        from shohoj_macro.ai.openrouter_client import OpenRouterClient
        from shohoj_macro.ai.captcha_solver import ReCaptchaSolver
        from shohoj_macro.ai.orchestrator import OperationOrchestrator
        
        import os
        proxy_dir = os.path.join(os.getcwd(), "proxies")
        os.makedirs(proxy_dir, exist_ok=True)
        self.proxy_manager = ProxySessionManager(proxy_dir=proxy_dir)
        self.ai_client = OpenRouterClient()
        self.captcha_solver = ReCaptchaSolver(self.player.cdp_bridge, self.ai_client)
        
        self.orchestrator = OperationOrchestrator(
            excel_engine=self.player.csv_engine,
            proxy_manager=self.proxy_manager,
            nst_controller=self.player.nst_controller,
            macro_player=self.player,
            ai_client=self.ai_client,
            captcha_solver=self.captcha_solver,
            cdp_bridge=self.player.cdp_bridge
        )

        # Settings
        self.settings = {
            "record_hotkey": "<f8>",
            "play_hotkey": "<f9>",
            "stop_hotkey": "<f10>",
            "humanizer_enabled": True,
            "bio_rhythm_enabled": True,
            "block_physical_input": False,
            "audio_cues_enabled": True,
            "auto_popup_hud": True,
            "countdown_enabled": False,
        }

        # HUD Window instance
        self.hud_window = None

        # Build UI Structure
        self._build_main_layout()
        self._build_status_bar()

        # Start Services
        self.hotkeys.start()
        self.browser_bridge.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.log_panel.log(f"Welcome to {__app_name__} v{__version__} by {__author__} ({__username__})", "SUCCESS")
        self.log_panel.log("Zero-AI Visual State Engine & CSV Data Dock Ready.", "INFO")
        self.log_panel.log("Global Hotkeys Active: F8 (Record), F9 (Play/Pause), F10 (Emergency Stop)", "INFO")

        # Background Update Check
        from shohoj_macro.core.updater import UpdateChecker
        UpdateChecker.check_for_updates_async(self._on_update_check_result)

    def _manual_check_updates(self):
        from shohoj_macro.core.updater import UpdateChecker
        self.log_panel.log("Checking GitHub Releases API for updates...", "INFO")
        def on_res(update_info):
            if update_info:
                self._on_update_check_result(update_info)
            else:
                self.after(0, lambda: messagebox.showinfo("Shohoj Macro Updates", f"You are running the latest version (v{__version__})."))
        UpdateChecker.check_for_updates_async(on_res)

    def _on_update_check_result(self, update_info):
        if not update_info:
            return
            
        def show_dialog():
            ver = update_info.get("version")
            title = update_info.get("title")
            url = update_info.get("html_url")
            download_url = update_info.get("download_url")
            changelog = update_info.get("changelog", "")
            
            self.log_panel.log(f"🚀 Remote Update Available: v{ver} ({title})", "WARN")
            
            msg = f"A new version of Shohoj Macro is available!\n\n" \
                  f"Current Version: v{__version__}\n" \
                  f"Latest Version: v{ver}\n\n" \
                  f"Click 'Yes' to Auto-Update now, 'No' to open GitHub download page, or 'Cancel' to skip."
                  
            res = messagebox.askyesnocancel(
                "🚀 Shohoj Macro Remote Update",
                msg
            )
            
            if res is True:
                try:
                    self.log_panel.log(f"Downloading and applying update v{ver}...", "INFO")
                    from shohoj_macro.core.updater import UpdateChecker
                    UpdateChecker.trigger_auto_update(download_url)
                except Exception as e:
                    messagebox.showerror("Update Error", f"Failed to auto-update: {e}\nOpening browser instead.")
                    import webbrowser
                    webbrowser.open(url)
            elif res is False:
                import webbrowser
                webbrowser.open(url)
                
        self.after(100, show_dialog)

    def _play_sound(self, sound_type="info"):

        """Plays subtle Windows audio feedback."""
        if not self.settings.get("audio_cues_enabled", True):
            return
        try:
            if sound_type == "record_start":
                winsound.Beep(880, 120)
            elif sound_type == "record_stop":
                winsound.Beep(587, 140)
            elif sound_type == "play_start":
                winsound.Beep(1046, 120)
            elif sound_type == "stop":
                winsound.Beep(440, 180)
        except Exception:
            pass

    
    def _build_main_layout(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=14, pady=4)

        # --- Sidebar ---
        self.sidebar = GlassCard(self.main_container, width=220, corner_radius=12)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)

        lbl_logo = ctk.CTkLabel(
            self.sidebar,
            text=f"⚡ {__app_name__}",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=16, weight="bold"),
            text_color=GlassTheme.ACCENT_CYAN,
        )
        lbl_logo.pack(pady=(20, 30))

        # Sidebar Buttons
        def create_nav_btn(text, command):
            btn = ctk.CTkButton(
                self.sidebar, text=text, command=command, fg_color="transparent",
                hover_color=GlassTheme.CARD_BG_SECONDARY, anchor="w",
                font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=13, weight="bold")
            )
            btn.pack(fill="x", padx=10, pady=5)
            return btn

        self.btn_nav_builder = create_nav_btn("🛠️ Builder Studio", lambda: self._switch_mode("builder"))
        self.btn_nav_ops = create_nav_btn("🚀 Operations", lambda: self._switch_mode("ops"))
        self.btn_nav_ai = create_nav_btn("🤖 AI Co-Pilot", lambda: self._switch_mode("ai"))
        
        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True, fill="both")
        
        self.btn_nav_export = create_nav_btn("📤 Export Macro", self._open_export)
        self.btn_nav_save = create_nav_btn("💾 Save Macro", self._save_macro)
        self.btn_nav_settings = create_nav_btn("⚙️ Settings", self._open_settings)
        self.btn_nav_updates = create_nav_btn("🚀 Check Updates", self._manual_check_updates)
        self.btn_nav_about = create_nav_btn("ℹ️ About", lambda: AboutDialog(self))


        # --- Content Area ---
        self.content_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)

        # 1. Builder Mode
        self.frame_builder = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._build_builder_mode()

        # 2. Operations Mode
        self.frame_ops = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._build_ops_mode()
        
        # 3. AI Mode
        self.frame_ai = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._build_ai_mode()

        # Default Mode
        self._switch_mode("builder")

    def _switch_mode(self, mode):
        self.frame_builder.pack_forget()
        self.frame_ops.pack_forget()
        self.frame_ai.pack_forget()
        
        self.btn_nav_builder.configure(fg_color="transparent")
        self.btn_nav_ops.configure(fg_color="transparent")
        self.btn_nav_ai.configure(fg_color="transparent")

        if mode == "builder":
            self.frame_builder.pack(fill="both", expand=True)
            self.btn_nav_builder.configure(fg_color=GlassTheme.CARD_BG_SECONDARY)
        elif mode == "ops":
            self.frame_ops.pack(fill="both", expand=True)
            self.btn_nav_ops.configure(fg_color=GlassTheme.CARD_BG_SECONDARY)
        elif mode == "ai":
            self.frame_ai.pack(fill="both", expand=True)
            self.btn_nav_ai.configure(fg_color=GlassTheme.CARD_BG_SECONDARY)

    def _build_builder_mode(self):
        # Top Toolbar
        toolbar = GlassCard(self.frame_builder, height=50, corner_radius=10)
        toolbar.pack(fill="x", pady=(0, 10))

        self.btn_record = ctk.CTkButton(toolbar, text="● Record (F8)", width=105, height=32, fg_color=GlassTheme.CARD_BG_SECONDARY, hover_color=GlassTheme.ACCENT_RED, text_color=GlassTheme.ACCENT_RED, command=self._toggle_record)
        self.btn_record.pack(side="left", padx=10, pady=9)

        self.btn_play = ctk.CTkButton(toolbar, text="▶ Play (F9)", width=95, height=32, fg_color=GlassTheme.CARD_BG_SECONDARY, hover_color=GlassTheme.ACCENT_EMERALD, text_color=GlassTheme.ACCENT_EMERALD, command=self._toggle_play)
        self.btn_play.pack(side="left", padx=3)

        self.btn_stop = ctk.CTkButton(toolbar, text="⏹ Stop (F10)", width=95, height=32, fg_color=GlassTheme.CARD_BG_SECONDARY, hover_color="#333A4D", command=self._stop_all)
        self.btn_stop.pack(side="left", padx=3)
        
        ctk.CTkLabel(toolbar, text="|", text_color=GlassTheme.CARD_BORDER).pack(side="left", padx=6)
        
        self.opt_rec_mode = ctk.CTkOptionMenu(toolbar, values=["Clicks & Keys (Clean)", "All Motion", "Keys Only"], width=135, height=28, command=self._on_rec_mode_changed)
        self.opt_rec_mode.set("Clicks & Keys (Clean)")
        self.opt_rec_mode.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(toolbar, text="|", text_color=GlassTheme.CARD_BORDER).pack(side="left", padx=6)

        # Loops input
        ctk.CTkLabel(toolbar, text="Loops:", font=ctk.CTkFont(size=11), text_color=GlassTheme.TEXT_SECONDARY).pack(side="left", padx=(2, 2))
        self.ent_loops = ctk.CTkEntry(toolbar, width=45, height=28, font=ctk.CTkFont(size=11))
        self.ent_loops.insert(0, "1")
        self.ent_loops.pack(side="left", padx=(0, 6))

        # Speed slider
        ctk.CTkLabel(toolbar, text="Speed:", font=ctk.CTkFont(size=11), text_color=GlassTheme.TEXT_SECONDARY).pack(side="left", padx=(2, 2))
        self.speed_slider = ctk.CTkSlider(toolbar, from_=0.2, to=5.0, number_of_steps=48, width=90, height=16, command=self._on_speed_changed)
        self.speed_slider.set(1.0)
        self.speed_slider.pack(side="left", padx=(0, 4))
        self.lbl_speed_val = ctk.CTkLabel(toolbar, text="1.0x", font=ctk.CTkFont(size=10, weight="bold"), width=30)
        self.lbl_speed_val.pack(side="left", padx=(0, 6))

        # Main Builder Content (Timeline + Right Panel)
        content = ctk.CTkFrame(self.frame_builder, fg_color="transparent")
        content.pack(fill="both", expand=True)

        self.timeline = TimelineTableEditor(content, csv_engine=self.player.csv_engine, on_events_modified=self._on_timeline_modified, on_step_selected=self._on_step_selected, on_trigger_snipper=self._launch_screen_snipper)
        self.timeline.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_panel = ctk.CTkFrame(content, width=310, fg_color="transparent")
        right_panel.pack(side="right", fill="y")
        
        self.trajectory_canvas = TrajectoryCanvas(right_panel, width=300, height=140)
        self.trajectory_canvas.pack(fill="x", pady=(0, 8))
        
        self.library_sidebar = MacroLibrarySidebar(right_panel, width=300, on_macro_selected=self._load_macro_from_path)
        self.library_sidebar.pack(fill="both", expand=True)

    def _build_ops_mode(self):
        # Left Scrollable Sidebar to fix bottom overflow on small windows/resizing
        left_col = ctk.CTkScrollableFrame(self.frame_ops, width=320, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=False, padx=(0, 10))

        right_col = ctk.CTkFrame(self.frame_ops, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True)

        self.browser_panel = BrowserCompanionPanel(right_col, on_inspect_web_element=self._start_browser_inspection)
        self.browser_panel.pack(fill="x", pady=(0, 8))

        # Tabview for Logs & CSV Data Trace
        self.ops_tabview = ctk.CTkTabview(
            right_col,
            segmented_button_selected_color=GlassTheme.ACCENT_CYAN,
            segmented_button_selected_hover_color=GlassTheme.ACCENT_CYAN,
        )
        self.ops_tabview.pack(fill="both", expand=True)

        tab_logs = self.ops_tabview.add("📋 Activity Logs")
        tab_csv_trace = self.ops_tabview.add("📊 CSV Data Trace")

        self.log_panel = PlaybackLogPanel(tab_logs)
        self.log_panel.pack(fill="both", expand=True)

        self.csv_trace_tab = CSVTraceTabFrame(tab_csv_trace, csv_engine=self.player.csv_engine)
        self.csv_trace_tab.pack(fill="both", expand=True)

        self.csv_dock = CSVDockPanel(left_col, csv_engine=self.player.csv_engine, on_dataset_changed=self._on_csv_dataset_changed)
        self.csv_dock.pack(fill="x", pady=(0, 10))

        self.ops_panel = OperationStudioPanel(
            left_col,
            orchestrator=self.orchestrator,
            log_panel=self.log_panel,
            show_settings_callback=self._open_settings,
            on_switch_to_builder=lambda: self._switch_mode("builder"),
        )
        self.ops_panel.pack(fill="x")

        # Link log panel & orchestrator callbacks
        self.ops_panel.log_panel = self.log_panel
        self.orchestrator.on_log = self.ops_panel._on_log
        self.orchestrator.on_waiting_manual_step = self._on_waiting_manual_step
        self.orchestrator.on_execution_state_change = self._on_op_execution_state_change
        self.ops_panel.on_range_changed = self.csv_trace_tab.set_target_range
        self.csv_trace_tab.on_set_start_row = self._on_set_start_row_from_trace

    def _on_set_start_row_from_trace(self, row_num: int):
        if hasattr(self, 'ops_panel'):
            self.ops_panel.entry_start_row.delete(0, "end")
            self.ops_panel.entry_start_row.insert(0, str(row_num))
            self.ops_panel._on_range_entry_changed()
            if self.log_panel:
                self.log_panel.log(f"Start Row set to {row_num} from CSV trace.", "INFO")

    def _on_op_execution_state_change(self, state: str, curr_row: int = 0, tot_rows: int = 0):
        if hasattr(self, 'ops_panel'):
            self.ops_panel.set_execution_state(state, curr_row, tot_rows)
        if hasattr(self, 'csv_trace_tab') and state == "RUNNING" and curr_row > 0:
            self.csv_trace_tab.set_active_row(curr_row - 1)

    def _build_ai_mode(self):
        lbl = ctk.CTkLabel(self.frame_ai, text="🧠 AI Co-Pilot Studio", font=ctk.CTkFont(size=20, weight="bold"))
        lbl.pack(pady=20)
        
        # We will embed the AI Wizard here, or provide a launch button.
        btn_launch = GlassButton(self.frame_ai, text="Launch AI Wizard", command=self._open_wizard, height=40, font=ctk.CTkFont(size=14, weight="bold"))
        btn_launch.pack(pady=20)
        
        self.lbl_ai_status = ctk.CTkLabel(self.frame_ai, text="AI Co-Pilot is currently implemented as a floating window.\\nClick above to launch it.", text_color=GlassTheme.TEXT_SECONDARY)
        self.lbl_ai_status.pack()

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=26, fg_color="transparent")
        self.status_bar.pack(fill="x", padx=18, pady=(0, 6))

        self.lbl_status = ctk.CTkLabel(
            self.status_bar,
            text="Ready • Shohoj Macro Studio",
            font=ctk.CTkFont(size=10),
            text_color=GlassTheme.TEXT_SECONDARY,
        )
        self.lbl_status.pack(side="left")

        lbl_credits = ctk.CTkLabel(
            self.status_bar,
            text=f"Developed with pride by {__author__} ({__username__})",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=GlassTheme.TEXT_MUTED,
        )
        lbl_credits.pack(side="right")
    # ================= Action Callbacks =================

    def _launch_screen_snipper(self):
        """Launches the interactive freeze-frame Screen Snipper."""
        self.withdraw()  # Temporarily hide studio window for clean capture

        def on_snip_completed(name: str, b64_str: str, conf: float, cx: int, cy: int):
            self.deiconify()
            # Create Visual Anchor MacroEvent
            ev = MacroEvent(
                event_type=EventType.VISUAL_ANCHOR_CLICK,
                x=cx,
                y=cy,
                template_name=name,
                template_base64=b64_str,
                confidence_threshold=conf,
                human_target_radius=8,
                delay_after_ms=200,
            )
            self.timeline.append_event_live(ev)
            self.trajectory_canvas.update_trajectory(self.timeline.get_events())
            self.log_panel.log(f"Added Visual Anchor '{name}' (Confidence: {int(conf*100)}%)", "SUCCESS")

        self.after(200, lambda: ScreenSnipperModal(self, on_snip_completed))

    def _on_csv_dataset_changed(self):
        count = self.player.csv_engine.get_row_count()
        if count > 0:
            self.ent_loops.delete(0, "end")
            self.ent_loops.insert(0, str(count))
            self.log_panel.log(f"CSV Dataset linked ({count} rows). Auto-set loops to {count}.", "SUCCESS")
            # Notify ops panel for Smart Start Row Memory
            if hasattr(self, 'ops_panel'):
                self.ops_panel.on_csv_loaded(self.player.csv_engine.filepath)
            if hasattr(self, 'csv_trace_tab'):
                self.csv_trace_tab.load_dataset()
                if hasattr(self, 'ops_panel'):
                    try:
                        s = int(self.ops_panel.entry_start_row.get().strip())
                        e = int(self.ops_panel.entry_end_row.get().strip())
                        self.csv_trace_tab.set_target_range(s, e)
                    except Exception:
                        pass
        else:
            self.log_panel.log("CSV Dataset unlinked.", "INFO")

    def _on_speed_changed(self, value):
        self.lbl_speed_val.configure(text=f"{value:.1f}x")

    def _on_rec_mode_changed(self, choice):
        if "Clean" in choice:
            self.recorder.recording_mode = "CLICKS_AND_KEYS"
        elif "Keys" in choice:
            self.recorder.recording_mode = "KEYS_ONLY"
        else:
            self.recorder.recording_mode = "ALL"
        self.log_panel.log(f"Recording Mode: {self.recorder.recording_mode}", "INFO")

    def _on_humanizer_toggle(self):
        enabled = bool(self.switch_humanizer.get())
        self.player.humanizer_enabled = enabled
        self.log_panel.log(f"Humanizer Kinematics {'Enabled' if enabled else 'Disabled'}", "INFO")

    def _on_hud_closed(self):
        self.hud_window = None

    def _show_hud_auto(self):
        if self.settings.get("auto_popup_hud", True):
            is_open = False
            if self.hud_window is not None:
                try:
                    is_open = bool(self.hud_window.winfo_exists())
                except Exception:
                    is_open = False
            if not is_open:
                try:
                    self.hud_window = DynamicIslandHUD(
                        self,
                        on_toggle_record=self._toggle_record,
                        on_toggle_play=self._toggle_play,
                        on_stop=self._stop_all,
                        on_close=self._on_hud_closed,
                    )
                except Exception:
                    self.hud_window = None

    def _toggle_record(self):
        if self.recorder.is_recording:
            events = self.recorder.stop()
            self.timeline.set_events(events)
            self.trajectory_canvas.update_trajectory(events)
            self.btn_record.configure(text="● Record (F8)", fg_color="#3A181C", text_color=GlassTheme.ACCENT_RED)
            self.lbl_status.configure(text=f"Recording stopped. Total {len(events)} actions captured.")
            self.log_panel.log(f"Recording stopped ({len(events)} events captured).", "SUCCESS")
            self._play_sound("record_stop")
            if self.hud_window:
                self.hud_window.update_status("IDLE")
        else:
            if self.player.is_playing():
                self.player.stop()

            self.timeline.set_events([])
            self.trajectory_canvas.update_trajectory([])

            mode_choice = self.opt_rec_mode.get()
            rec_mode = "CLICKS_AND_KEYS" if "Clean" in mode_choice else ("KEYS_ONLY" if "Keys" in mode_choice else "ALL")

            self.recorder.start(mode=rec_mode)
            self.btn_record.configure(text="⏹ Stop Rec (F8)", fg_color=GlassTheme.ACCENT_RED, text_color="#FFFFFF")
            self.lbl_status.configure(text="● Recording inputs live... Press F8 to Stop.")
            self.log_panel.log(f"Recording started ({rec_mode}). Move, click or type...", "INFO")
            self._play_sound("record_start")

            self._show_hud_auto()
            if self.hud_window:
                self.hud_window.update_status("RECORDING", "00:00", count=0)

    def _toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            self.btn_play.configure(text="▶ Resume (F9)", fg_color="#182A3A", text_color=GlassTheme.ACCENT_CYAN)
            self.lbl_status.configure(text="Playback Paused.")
            if self.hud_window:
                self.hud_window.update_status("PAUSED")
        elif self.player.is_paused():
            self.player.resume()
            self.btn_play.configure(text="⏸ Pause (F9)", fg_color="#3A2814", text_color=GlassTheme.ACCENT_ORANGE)
            self.lbl_status.configure(text="Playback Resumed...")
            if self.hud_window:
                self.hud_window.update_status("PLAYING")
        else:
            events = self.timeline.get_events()
            if not events:
                messagebox.showwarning("No Actions", "Please record or add actions first before playing.")
                return

            try:
                loops = int(self.ent_loops.get())
            except ValueError:
                loops = 1
            speed = float(self.speed_slider.get())

            self.player.play(events, loops=loops, speed=speed)
            self.btn_play.configure(text="⏸ Pause (F9)", fg_color="#3A2814", text_color=GlassTheme.ACCENT_ORANGE)
            self.lbl_status.configure(text=f"Playing macro ({loops} loops at {speed:.1f}x speed)...")
            self._play_sound("play_start")

            self._show_hud_auto()
            if self.hud_window:
                self.hud_window.update_status("PLAYING", f"Loop 1/{loops}")

    def _stop_all(self):
        if hasattr(self, 'orchestrator'):
            self.orchestrator.stop()
        if self.recorder.is_recording:
            self._toggle_record()
        if self.player.is_playing() or self.player.is_paused():
            self.player.stop()
            self.btn_play.configure(text="▶ Play (F9)", fg_color="#143A22", text_color=GlassTheme.ACCENT_EMERALD)
            self.lbl_status.configure(text="Playback Stopped.")
            self.log_panel.log("Playback terminated by user.", "WARN")
            self._play_sound("stop")
            if self.hud_window:
                self.hud_window.update_status("IDLE")

    def _hotkey_toggle_record(self):
        self.after(0, self._toggle_record)

    def _hotkey_toggle_play(self):
        # If the Orchestrator is waiting for manual verification, F9 acts as 'Mark Done & Next'
        if hasattr(self, 'orchestrator') and getattr(self.orchestrator, 'is_waiting_manual_step', lambda: False)():
            if hasattr(self, 'ops_panel'):
                self.after(0, self.ops_panel.resume_done_op)
                return
        self.after(0, self._toggle_play)

    def _on_waiting_manual_step(self, row_num: int):
        def _update():
            self._play_sound("record_stop")
            self.lbl_status.configure(text=f"🔔 Row {row_num} filled! Waiting for manual check... Press F9 or click 'Done'.")
            if self.hud_window:
                self.hud_window.update_status("WAITING_MANUAL", f"Row {row_num}")
            if hasattr(self, 'csv_trace_tab'):
                self.csv_trace_tab.set_active_row(row_num - 1)
        self.after(0, _update)

    def _hotkey_stop(self):
        self.after(0, self._stop_all)

    def _on_event_recorded(self, ev: MacroEvent):
        def _add_live():
            self.timeline.append_event_live(ev)
            self.trajectory_canvas.update_trajectory(self.timeline.get_events())
            count = len(self.timeline.get_events())
            self.lbl_status.configure(text=f"● Recording... [{count} actions captured]")
            if self.hud_window:
                self.hud_window.update_status("RECORDING", count=count)

        self.after(0, _add_live)

    def _on_step_started(self, step_idx: int, ev: MacroEvent):
        self.after(0, lambda: self.timeline.highlight_step(step_idx))
        self.after(0, lambda: self.trajectory_canvas.update_trajectory(self.timeline.get_events(), step_idx))

    def _on_loop_completed(self, current: int, total: int):
        tot_str = str(total) if total > 0 else "∞"
        self.after(0, lambda: self.log_panel.log(f"Completed loop {current}/{tot_str}", "SUCCESS"))
        if self.hud_window:
            self.after(0, lambda: self.hud_window.update_status("PLAYING", f"Loop {current}/{tot_str}"))

    def _on_playback_finished(self, success: bool, err: str):
        def _finish():
            self.btn_play.configure(text="▶ Play (F9)", fg_color="#143A22", text_color=GlassTheme.ACCENT_EMERALD)
            if success:
                self.lbl_status.configure(text="Playback completed successfully.")
                self.log_panel.log("Playback finished successfully.", "SUCCESS")
                self._play_sound("record_stop")
            else:
                self.lbl_status.configure(text=f"Playback aborted: {err}")
                self.log_panel.log(f"Playback failed: {err}", "ERROR")
                self._play_sound("stop")
            if self.hud_window:
                self.hud_window.update_status("IDLE")

        try:
            self.after(0, _finish)
        except Exception:
            pass

    def _on_log_message(self, msg: str, level: str):
        try:
            self.after(0, lambda: self.log_panel.log(msg, level))
        except Exception:
            pass

    def _on_timeline_modified(self):
        events = self.timeline.get_events()
        self.trajectory_canvas.update_trajectory(events)

    def _on_step_selected(self, idx: int):
        events = self.timeline.get_events()
        self.trajectory_canvas.update_trajectory(events, idx)

    def _toggle_dynamic_island(self):
        is_open = False
        if self.hud_window is not None:
            try:
                is_open = bool(self.hud_window.winfo_exists())
            except Exception:
                is_open = False

        if is_open:
            try:
                self.hud_window.destroy()
            except Exception:
                pass
            self.hud_window = None
        else:
            try:
                self.hud_window = DynamicIslandHUD(
                    self,
                    on_toggle_record=self._toggle_record,
                    on_toggle_play=self._toggle_play,
                    on_stop=self._stop_all,
                    on_close=self._on_hud_closed,
                )
            except Exception as e:
                self.hud_window = None
                self.log_panel.log(f"HUD init notice: {e}", "WARNING")

    def _start_browser_inspection(self):
        self.browser_bridge.send_broadcast({"action": "START_ELEMENT_INSPECTOR"})
        self.log_panel.log("Browser DOM Inspector activated. Click on any web element in Chrome/Edge.", "INFO")

    def _on_browser_element_picked(self, data: dict):
        def _add():
            screen_x = data.get("screenX", 500)
            screen_y = data.get("screenY", 500)
            selector = data.get("cssSelector", "")
            desc = data.get("textContent", "Web Element")
            
            if selector:
                # v3.5: Auto-create CDP action
                ev = MacroEvent(
                    event_type=EventType.CDP_PHYSICAL_INPUT,
                    selector=selector,
                    comment=f"CDP: {desc[:20]}",
                    delay_after_ms=200,
                )
                self.log_panel.log(f"Captured CDP Element: '{selector}'", "SUCCESS")
            else:
                ev = MacroEvent(
                    event_type=EventType.MOUSE_CLICK,
                    x=screen_x,
                    y=screen_y,
                    human_target_radius=10,
                    comment=f"Web: {desc}",
                    delay_after_ms=200,
                )
                self.log_panel.log(f"Captured Web Element at ({screen_x}, {screen_y})", "SUCCESS")
                
            self.timeline.append_event_live(ev)
            self.trajectory_canvas.update_trajectory(self.timeline.get_events())

        self.after(0, _add)

    def _on_browser_status_change(self, connected: bool):
        self.after(0, lambda: self.browser_panel.set_connected(connected))

    def _save_macro(self):
        events = self.timeline.get_events()
        if not events:
            messagebox.showwarning("Empty", "No actions in timeline to save.")
            return

        default_dir = MacroStorage.get_default_library_dir()
        path = filedialog.asksaveasfilename(
            initialdir=default_dir,
            defaultextension=".shj",
            filetypes=[("Shohoj Macro Files", "*.shj")],
        )
        if path:
            name = os.path.splitext(os.path.basename(path))[0]
            MacroStorage.save_macro_to_file(path, events, name=name)
            self.library_sidebar.refresh_library()
            self.log_panel.log(f"Macro saved to '{path}'", "SUCCESS")

    def _load_macro_from_path(self, path: str):
        try:
            events, meta = MacroStorage.load_macro_from_file(path)
            self.timeline.set_events(events)
            self.trajectory_canvas.update_trajectory(events)
            self.log_panel.log(f"Loaded macro '{meta.get('name', 'Untitled')}' ({len(events)} actions)", "INFO")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load macro: {e}")

    def _open_settings(self):
        def on_save(s):
            self.settings = s
            self.player.humanizer_enabled = s["humanizer_enabled"]
            self.player.bio_rhythm_enabled = s["bio_rhythm_enabled"]
            self.player.block_physical_input = s["block_physical_input"]
            self.hotkeys.update_hotkeys(s["record_hotkey"], s["play_hotkey"], s["stop_hotkey"])
            self.recorder.set_ignored_keys([s["record_hotkey"], s["play_hotkey"], s["stop_hotkey"]])
            self.log_panel.log("Settings updated successfully.", "SUCCESS")

        SettingsDialog(self, self.settings, on_save)

    def _open_wizard(self):
        def on_wizard_complete(events):
            self.timeline.set_events(events)
            self.trajectory_canvas.update_trajectory(events)
            self.log_panel.log(f"AI Co-Pilot generated {len(events)} steps.", "SUCCESS")
            
        # Needs orchestrator's cdp_bridge, nst_controller, and ai client
        AITrainingWizard(self, self.orchestrator.cdp, self.player.nst_controller, self.orchestrator.ai, on_wizard_complete)

    def _open_export(self):
        events = self.timeline.get_events()
        if not events:
            messagebox.showwarning("Empty", "No actions to export.")
            return

        def on_fmt(fmt):
            ext = ".py" if fmt == "python" else ".ahk"
            path = filedialog.asksaveasfilename(
                defaultextension=ext,
                filetypes=[(f"{fmt.upper()} Script", f"*{ext}")],
            )
            if path:
                if fmt == "python":
                    MacroExporter.export_to_python_script(events, path)
                else:
                    MacroExporter.export_to_ahk_script(events, path)
                self.log_panel.log(f"Exported script to '{path}'", "SUCCESS")

        ExportDialog(self, on_fmt)

    def _on_close(self):
        self._stop_all()
        if hasattr(self, 'orchestrator'):
            try:
                self.orchestrator.stop()
            except Exception:
                pass
        if self.hud_window and self.hud_window.winfo_exists():
            try:
                self.hud_window.destroy()
            except Exception:
                pass
        self.hotkeys.stop()
        self.browser_bridge.stop()
        self.destroy()
