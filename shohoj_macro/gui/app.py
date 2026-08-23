"""
Shohoj Macro - Main Studio Window (Apple-Style Glassmorphism UI)
Developed by Polash Khan (ypolash2)
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from datetime import datetime

from shohoj_macro.gui.glass_theme import GlassTheme, GlassCard, GlassButton
from shohoj_macro.gui.timeline_table import TimelineTableEditor
from shohoj_macro.gui.trajectory_canvas import TrajectoryCanvas
from shohoj_macro.gui.playback_log import PlaybackLogPanel
from shohoj_macro.gui.dynamic_island import DynamicIslandHUD
from shohoj_macro.gui.macro_library import MacroLibrarySidebar
from shohoj_macro.gui.browser_panel import BrowserCompanionPanel
from shohoj_macro.gui.settings_dialog import SettingsDialog
from shohoj_macro.gui.export_dialog import ExportDialog
from shohoj_macro.gui.about_dialog import AboutDialog

from shohoj_macro.core.events import MacroEvent, EventType
from shohoj_macro.core.recorder import MacroRecorder
from shohoj_macro.core.player import MacroPlayer, PlaybackState
from shohoj_macro.core.storage import MacroStorage
from shohoj_macro.core.exporter import MacroExporter
from shohoj_macro.core.hotkeys import GlobalHotkeyManager
from shohoj_macro.core.browser_bridge import BrowserBridgeServer
from shohoj_macro.utils.dpi_helper import init_dpi_awareness
from shohoj_macro.version import __app_name__, __version__, __author__, __username__


class ShohojMacroStudio(ctk.CTk):
    """Master Application Window."""

    def __init__(self):
        super().__init__()
        init_dpi_awareness()
        GlassTheme.apply_global_settings()

        self.title(f"{__app_name__} v{__version__} • Studio")
        self.geometry("1180x720")
        self.minsize(980, 620)
        self.configure(fg_color=GlassTheme.BG_DARK)

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

        # Settings
        self.settings = {
            "record_hotkey": "<f8>",
            "play_hotkey": "<f9>",
            "stop_hotkey": "<f10>",
            "humanizer_enabled": True,
            "bio_rhythm_enabled": True,
            "block_physical_input": False,
        }

        # HUD Window instance
        self.hud_window = None

        # Build UI Structure
        self._build_top_ribbon()
        self._build_main_layout()
        self._build_status_bar()

        # Start Services
        self.hotkeys.start()
        self.browser_bridge.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.log_panel.log(f"Welcome to {__app_name__} v{__version__} by {__author__} ({__username__})", "SUCCESS")
        self.log_panel.log("Global Hotkeys Active: F8 (Record), F9 (Play/Pause), F10 (Emergency Stop)", "INFO")

    def _build_top_ribbon(self):
        self.ribbon = GlassCard(self, height=58, corner_radius=12)
        self.ribbon.pack(fill="x", padx=14, pady=(12, 6))

        # Brand / Logo
        lbl_logo = ctk.CTkLabel(
            self.ribbon,
            text=f"⚡ {__app_name__}",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=15, weight="bold"),
            text_color=GlassTheme.ACCENT_CYAN,
        )
        lbl_logo.pack(side="left", padx=(14, 16))

        # Record Button
        self.btn_record = ctk.CTkButton(
            self.ribbon,
            text="● Record (F8)",
            width=105,
            height=32,
            corner_radius=10,
            fg_color="#3A181C",
            hover_color=GlassTheme.ACCENT_RED,
            text_color=GlassTheme.ACCENT_RED,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
            command=self._toggle_record,
        )
        self.btn_record.pack(side="left", padx=4)

        # Play Button
        self.btn_play = ctk.CTkButton(
            self.ribbon,
            text="▶ Play (F9)",
            width=95,
            height=32,
            corner_radius=10,
            fg_color="#143A22",
            hover_color=GlassTheme.ACCENT_EMERALD,
            text_color=GlassTheme.ACCENT_EMERALD,
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
            command=self._toggle_play,
        )
        self.btn_play.pack(side="left", padx=4)

        # Stop Button
        self.btn_stop = ctk.CTkButton(
            self.ribbon,
            text="⏹ Stop (F10)",
            width=95,
            height=32,
            corner_radius=10,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold"),
            command=self._stop_all,
        )
        self.btn_stop.pack(side="left", padx=4)

        # Separator
        ctk.CTkLabel(self.ribbon, text="|", text_color=GlassTheme.CARD_BORDER).pack(side="left", padx=8)

        # Loops input
        ctk.CTkLabel(self.ribbon, text="Loops:", font=ctk.CTkFont(size=11), text_color=GlassTheme.TEXT_SECONDARY).pack(side="left", padx=(2, 4))
        self.ent_loops = ctk.CTkEntry(self.ribbon, width=44, height=28)
        self.ent_loops.insert(0, "1")
        self.ent_loops.pack(side="left", padx=(0, 8))

        # Speed Slider
        ctk.CTkLabel(self.ribbon, text="Speed:", font=ctk.CTkFont(size=11), text_color=GlassTheme.TEXT_SECONDARY).pack(side="left", padx=(2, 4))
        self.speed_slider = ctk.CTkSlider(self.ribbon, from_=0.2, to=3.0, number_of_steps=28, width=85, command=self._on_speed_changed)
        self.speed_slider.set(1.0)
        self.speed_slider.pack(side="left", padx=(0, 2))
        self.lbl_speed_val = ctk.CTkLabel(self.ribbon, text="1.0x", font=ctk.CTkFont(size=10, weight="bold"), text_color=GlassTheme.TEXT_PRIMARY, width=32)
        self.lbl_speed_val.pack(side="left", padx=(0, 8))

        # Humanizer Toggle Switch
        self.switch_humanizer = ctk.CTkSwitch(
            self.ribbon,
            text="Humanize",
            font=ctk.CTkFont(size=11, weight="bold"),
            progress_color=GlassTheme.ACCENT_PURPLE,
            command=self._on_humanizer_toggle,
        )
        self.switch_humanizer.select()
        self.switch_humanizer.pack(side="left", padx=4)

        # Right Side Tools
        self.btn_about = ctk.CTkButton(
            self.ribbon,
            text="ℹ️",
            width=32,
            height=30,
            corner_radius=8,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            command=lambda: AboutDialog(self),
        )
        self.btn_about.pack(side="right", padx=(2, 10))

        self.btn_settings = ctk.CTkButton(
            self.ribbon,
            text="⚙️",
            width=32,
            height=30,
            corner_radius=8,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            command=self._open_settings,
        )
        self.btn_settings.pack(side="right", padx=2)

        self.btn_export = ctk.CTkButton(
            self.ribbon,
            text="📤 Export",
            width=68,
            height=30,
            corner_radius=8,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color=GlassTheme.ACCENT_BLUE,
            command=self._open_export,
        )
        self.btn_export.pack(side="right", padx=2)

        self.btn_hud = ctk.CTkButton(
            self.ribbon,
            text="🏝️ Mini HUD",
            width=85,
            height=30,
            corner_radius=8,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color=GlassTheme.ACCENT_CYAN,
            command=self._toggle_dynamic_island,
        )
        self.btn_hud.pack(side="right", padx=2)

        self.btn_save = ctk.CTkButton(
            self.ribbon,
            text="💾 Save",
            width=60,
            height=30,
            corner_radius=8,
            fg_color=GlassTheme.CARD_BG_SECONDARY,
            hover_color="#333A4D",
            command=self._save_macro,
        )
        self.btn_save.pack(side="right", padx=2)

    def _build_main_layout(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=14, pady=4)

        # 1. Left Sidebar: Macro Library
        self.library_sidebar = MacroLibrarySidebar(
            self.main_container,
            width=180,
            on_macro_selected=self._load_macro_from_path,
        )
        self.library_sidebar.pack(side="left", fill="y", padx=(0, 8))

        # 2. Center: Timeline Table Editor
        self.timeline = TimelineTableEditor(
            self.main_container,
            on_events_modified=self._on_timeline_modified,
            on_step_selected=self._on_step_selected,
        )
        self.timeline.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # 3. Right Side: Visualizer, Browser Panel & Log
        self.right_panel = ctk.CTkFrame(self.main_container, width=300, fg_color="transparent")
        self.right_panel.pack(side="right", fill="y")

        self.trajectory_canvas = TrajectoryCanvas(self.right_panel, width=290, height=140)
        self.trajectory_canvas.pack(fill="x", pady=(0, 8))

        self.browser_panel = BrowserCompanionPanel(
            self.right_panel,
            on_inspect_web_element=self._start_browser_inspection,
        )
        self.browser_panel.pack(fill="x", pady=(0, 8))

        self.log_panel = PlaybackLogPanel(self.right_panel, height=180)
        self.log_panel.pack(fill="both", expand=True)

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

    def _on_speed_changed(self, value):
        self.lbl_speed_val.configure(text=f"{value:.1f}x")

    def _on_humanizer_toggle(self):
        enabled = bool(self.switch_humanizer.get())
        self.player.humanizer_enabled = enabled
        self.log_panel.log(f"Humanizer Physics {'Enabled' if enabled else 'Disabled'}", "INFO")

    def _toggle_record(self):
        if self.recorder.is_recording:
            events = self.recorder.stop()
            self.timeline.set_events(events)
            self.trajectory_canvas.update_trajectory(events)
            self.btn_record.configure(text="● Record (F8)", fg_color="#3A181C", text_color=GlassTheme.ACCENT_RED)
            self.lbl_status.configure(text=f"Recording stopped. Captured {len(events)} actions.")
            self.log_panel.log(f"Recording stopped ({len(events)} events captured).", "SUCCESS")
            if self.hud_window:
                self.hud_window.update_status("IDLE")
        else:
            if self.player.is_playing():
                self.player.stop()
            self.recorder.start(record_moves=True)
            self.btn_record.configure(text="⏹ Stop Rec", fg_color=GlassTheme.ACCENT_RED, text_color="#FFFFFF")
            self.lbl_status.configure(text="● Recording inputs... Press F8 to Stop.")
            self.log_panel.log("Recording started... Move, click or type.", "INFO")
            if self.hud_window:
                self.hud_window.update_status("RECORDING", "00:00")

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
            if self.hud_window:
                self.hud_window.update_status("PLAYING", f"Loop 1/{loops}")

    def _stop_all(self):
        if self.recorder.is_recording:
            self._toggle_record()
        if self.player.is_playing() or self.player.is_paused():
            self.player.stop()
            self.btn_play.configure(text="▶ Play (F9)", fg_color="#143A22", text_color=GlassTheme.ACCENT_EMERALD)
            self.lbl_status.configure(text="Playback Stopped.")
            self.log_panel.log("Playback terminated by user.", "WARN")
            if self.hud_window:
                self.hud_window.update_status("IDLE")

    def _hotkey_toggle_record(self):
        self.after(0, self._toggle_record)

    def _hotkey_toggle_play(self):
        self.after(0, self._toggle_play)

    def _hotkey_stop(self):
        self.after(0, self._stop_all)

    def _on_event_recorded(self, ev: MacroEvent):
        # Update timeline in real-time if necessary
        pass

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
            else:
                self.lbl_status.configure(text=f"Playback aborted: {err}")
                self.log_panel.log(f"Playback failed: {err}", "ERROR")
            if self.hud_window:
                self.hud_window.update_status("IDLE")

        self.after(0, _finish)

    def _on_log_message(self, msg: str, level: str):
        self.after(0, lambda: self.log_panel.log(msg, level))

    def _on_timeline_modified(self):
        events = self.timeline.get_events()
        self.trajectory_canvas.update_trajectory(events)

    def _on_step_selected(self, idx: int):
        events = self.timeline.get_events()
        self.trajectory_canvas.update_trajectory(events, idx)

    def _toggle_dynamic_island(self):
        if self.hud_window and self.hud_window.winfo_exists():
            self.hud_window.destroy()
            self.hud_window = None
        else:
            self.hud_window = DynamicIslandHUD(
                self,
                on_toggle_record=self._toggle_record,
                on_toggle_play=self._toggle_play,
                on_stop=self._stop_all,
            )

    def _start_browser_inspection(self):
        self.browser_bridge.send_broadcast({"action": "START_ELEMENT_INSPECTOR"})
        self.log_panel.log("Browser DOM Inspector activated. Click on any web element in Chrome/Edge.", "INFO")

    def _on_browser_element_picked(self, data: dict):
        def _add():
            screen_x = data.get("screenX", 500)
            screen_y = data.get("screenY", 500)
            desc = data.get("textContent") or data.get("cssSelector", "Web Element")
            ev = MacroEvent(
                event_type=EventType.MOUSE_CLICK,
                x=screen_x,
                y=screen_y,
                human_target_radius=12,
                comment=f"Web: {desc}",
                delay_after_ms=250,
            )
            evs = self.timeline.get_events()
            evs.append(ev)
            self.timeline.set_events(evs)
            self.trajectory_canvas.update_trajectory(evs)
            self.log_panel.log(f"Captured Web Element: '{desc}' at ({screen_x}, {screen_y})", "SUCCESS")

        self.after(0, _add)

    def _on_browser_status_change(self, connected: bool):
        self.after(0, lambda: self.browser_panel.set_connected(connected))

    def _save_macro(self):
        events = self.timeline.get_events()
        if not events:
            messagebox.showwarning("Empty", "No actions to save.")
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
            self.log_panel.log("Settings updated successfully.", "SUCCESS")

        SettingsDialog(self, self.settings, on_save)

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
        self.hotkeys.stop()
        self.browser_bridge.stop()
        self.destroy()
