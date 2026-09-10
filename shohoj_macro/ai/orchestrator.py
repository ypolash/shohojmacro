import time
import threading
import copy
import os
import re
from typing import Callable, Optional
from shohoj_macro.core.excel_engine import ExcelDataEngine
from shohoj_macro.core.csv_engine import CSVDataEngine
from shohoj_macro.core.proxy_manager import ProxySessionManager
from shohoj_macro.core.nst_controller import NSTController
from shohoj_macro.core.cdp_spatial_bridge import CDPSpatialBridge
from shohoj_macro.core.player import MacroPlayer
from shohoj_macro.core.events import MacroEvent, EventType
from shohoj_macro.core.country_mapper import CountryMapper
from shohoj_macro.core.name_splitter import NameSplitter
from shohoj_macro.ai.openrouter_client import OpenRouterClient
from shohoj_macro.ai.captcha_solver import ReCaptchaSolver
from shohoj_macro.core.storage import MacroStorage
from shohoj_macro.core.settings_manager import SettingsManager

try:
    import winsound
except ImportError:
    winsound = None


class OperationOrchestrator:
    """
    Master controller that executes multi-phase operations.
    Supports semi-automated form-filling, manual step pause/resume,
    custom confirmation word tagging ('Polash'), and dynamic row completion actions.
    """

    def __init__(self,
                 excel_engine: ExcelDataEngine,
                 proxy_manager: ProxySessionManager,
                 nst_controller: NSTController,
                 macro_player: MacroPlayer,
                 ai_client: OpenRouterClient,
                 captcha_solver: ReCaptchaSolver,
                 cdp_bridge: CDPSpatialBridge):

        self.excel = excel_engine
        self.proxy_manager = proxy_manager
        self.nst = nst_controller
        self.player = macro_player
        self.ai = ai_client
        self.captcha = captcha_solver
        self.cdp = cdp_bridge

        self._stop_requested = False
        self._manual_resume_event = threading.Event()
        self._is_waiting_manual = False
        self._current_conf_word = "Polash"
        self._current_action = "➡️ Move to Next Row"

        self.on_log: Optional[Callable[[str], None]] = None
        self.on_supervised_intercept: Optional[Callable[[MacroEvent, Callable[[bool], None]], None]] = None
        self.on_waiting_manual_step: Optional[Callable[[int], None]] = None
        self.on_execution_state_change: Optional[Callable[[str, int, int], None]] = None

    def log(self, msg: str, level: str = "INFO"):
        if self.on_log:
            try:
                self.on_log(msg)
            except Exception:
                pass
        else:
            try:
                print(f"[{level}] [Orchestrator] {msg}")
            except UnicodeEncodeError:
                safe_msg = msg.encode("ascii", "replace").decode("ascii")
                print(f"[{level}] [Orchestrator] {safe_msg}")

    def _notify_state(self, state: str, curr_row: int = 0, end_row: int = 0):
        if self.on_execution_state_change:
            try:
                self.on_execution_state_change(state, curr_row, end_row)
            except Exception:
                pass

    def is_waiting_manual_step(self) -> bool:
        """Returns True if the orchestrator is currently waiting for user verification."""
        return self._is_waiting_manual

    def resume_manual_step(self, conf_word: str = "Polash", action: str = "➡️ Move to Next Row"):
        """Called by GUI or Floating HUD when the user completes manual interaction."""
        if conf_word:
            self._current_conf_word = conf_word
        if action:
            self._current_action = action

        self._is_waiting_manual = False
        self._manual_resume_event.set()

    def stop(self):
        """Terminates active operations and clears wait conditions to prevent deadlocks."""
        self._stop_requested = True
        self._is_waiting_manual = False
        self._manual_resume_event.set()  # Unblock thread if paused
        self.player.stop()
        self._notify_state("STOPPED")

    def execute_operation(self,
                          start_row: int = 1,
                          end_row: int = 9999,
                          macro_path: str = "",
                          target_url: str = "",
                          test_run: bool = False,
                          supervised: bool = False,
                          auto_launch_profiles: bool = False,
                          semi_automated: bool = True,
                          confirmation_word: str = "Polash",
                          completion_action: str = "➡️ Move to Next Row",
                          profile_column: str = ""):
        """Execute operation across dataset rows in a background worker thread."""
        self._stop_requested = False
        self._manual_resume_event.clear()
        self._is_waiting_manual = False
        self._current_conf_word = confirmation_word or "Polash"
        self._current_action = completion_action or "➡️ Move to Next Row"

        self.player.supervised_mode = supervised
        self.player.on_supervised_intercept = self._handle_intercept
        self.auto_launch_profiles = auto_launch_profiles

        if not macro_path:
            self.log("Error: No macro file selected.", "ERROR")
            self._notify_state("IDLE")
            return

        total_rows = self.excel.get_row_count()
        if total_rows < 1:
            self.log("No data rows found in dataset to process.", "WARNING")
            self._notify_state("IDLE")
            return

        is_csv = isinstance(self.excel, CSVDataEngine) or hasattr(self.excel, 'rows')

        # Normalize row bounds
        if is_csv:
            start_row = max(1, start_row)
            if start_row > total_rows:
                self.log(f"Start row {start_row} exceeds total dataset rows ({total_rows}).", "ERROR")
                self._notify_state("IDLE")
                return
            end_row = min(end_row, total_rows)
        else:
            start_row = max(2, start_row)
            if start_row > total_rows:
                self.log(f"Start row {start_row} exceeds total Excel rows ({total_rows}).", "ERROR")
                self._notify_state("IDLE")
                return
            end_row = min(end_row, total_rows)

        if test_run:
            end_row = start_row

        self._notify_state("RUNNING", start_row, end_row)

        thread = threading.Thread(
            target=self._run_loop,
            args=(start_row, end_row, macro_path, target_url, semi_automated, is_csv, profile_column),
            daemon=True
        )
        thread.start()

    def _handle_intercept(self, event, resume_callback):
        if self.on_supervised_intercept:
            self.on_supervised_intercept(event, resume_callback)
        else:
            resume_callback(True)

    def _run_loop(self, start_row: int, end_row: int, macro_path: str, target_url: str, semi_automated: bool, is_csv: bool, profile_column: str = ""):
        self.log(f"Starting Operation from Row {start_row} to {end_row} (Semi-Auto: {semi_automated})")

        try:
            template_events, _ = MacroStorage.load_macro_from_file(macro_path)
            self.log(f"Loaded {len(template_events)} events from macro template.")
        except Exception as e:
            self.log(f"Failed to load macro: {e}", "ERROR")
            self._notify_state("IDLE")
            return

        # Pre-Flight: Check if CDP actions exist in this macro template
        needs_cdp = any(ev.event_type in (EventType.CDP_PHYSICAL_INPUT, EventType.AI_CAPTCHA_SOLVE) for ev in template_events)
        if needs_cdp and not getattr(self, 'auto_launch_profiles', False):
            is_alive = False
            if getattr(self.cdp, '_connected', False) and hasattr(self.cdp, 'is_alive'):
                is_alive = self.cdp.is_alive()

            if not is_alive:
                self.log("Macro requires browser DOM/CDP actions. Probing for running browser...")
                ws_url = self.nst.find_running_browser_ws_url()
                if ws_url:
                    self.cdp.connect(ws_url)
                    is_alive = hasattr(self.cdp, 'is_alive') and self.cdp.is_alive()

            if not is_alive:
                self.log("❌ Execution Aborted: Macro contains CDP web element actions, but no browser is connected or listening on a debugging port.", "ERROR")
                self.log("💡 Tip: Launch Chrome with '--remote-debugging-port=9222' or enable 'Auto-Launch NST Profiles'.", "INFO")
                self._notify_state("IDLE")
                return

        curr_row = start_row

        while curr_row <= end_row:
            if self._stop_requested:
                self.log("Operation stopped by user.")
                break

            internal_idx = (curr_row - 1) if is_csv else curr_row
            display_row = curr_row

            self._notify_state("RUNNING", display_row, end_row)
            self.log(f"--- Processing Row {display_row} ---")

            try:
                # PHASE 1: Data Load
                raw_data = self.excel.get_row_data(internal_idx)
                non_empty = [v for k, v in raw_data.items() if v and not str(k).startswith('_')]
                if not raw_data or not non_empty:
                    self.log(f"Row {display_row} is empty. Skipping.")
                    curr_row += 1
                    continue

                self.excel.mark_row_status(internal_idx, "Status", "IN PROGRESS")

                # PHASE 2: NST Profile Setup & Launch (Optional)
                if getattr(self, 'auto_launch_profiles', False):
                    country_name = raw_data.get("COUNTRY", "") or raw_data.get("Country", "")
                    session_filename = CountryMapper.get_session_filename(country_name)

                    try:
                        self.proxy_manager.load_session_file(session_filename)
                    except FileNotFoundError:
                        self.log(f"Proxy file {session_filename} not found. Proceeding with default proxy.")

                    proxy = self.proxy_manager.get_random_proxy()
                    proxy_str = proxy.raw_string if proxy else ""

                    # Resolve profile search email/name from specified column or fallbacks
                    sm = SettingsManager()
                    target_col = profile_column or sm.get("nst", "profile_column", "")
                    email = ""
                    if target_col and raw_data.get(target_col):
                        email = str(raw_data.get(target_col)).strip()
                    else:
                        for key in ["Email", "email", "EMAIL", "Username", "username", "User", "user", "Profile", "profile"]:
                            if raw_data.get(key):
                                email = str(raw_data.get(key)).strip()
                                break
                    if not email:
                        email = f"user_{display_row}"

                    self.log(f"Searching & launching NST profile for '{email}'...")

                    ws_url = self.nst.prepare_and_launch(email, proxy_str)
                    if ws_url:
                        self.cdp.connect(ws_url)
                        self.log(f"✅ CDP connected to NST profile '{email}'", "SUCCESS")
                    else:
                        raise Exception(f"Failed to obtain debug URL for NST profile '{email}'")
                else:
                    # Check if existing connection is still responsive
                    is_current_alive = False
                    if getattr(self.cdp, 'ws_url', None) and hasattr(self.cdp, 'is_alive'):
                        is_current_alive = self.cdp.is_alive()

                    # If not alive or fresh profile needed, search and poll for the newly opened browser
                    if not is_current_alive:
                        self.log("Waiting for fresh NST browser profile to open...", "INFO")
                        found_ws = None
                        for poll_idx in range(30):
                            if self._stop_requested:
                                break
                            found_ws = self.nst.find_running_browser_ws_url()
                            if found_ws:
                                break
                            time.sleep(0.5)

                        if found_ws:
                            self.cdp.connect(found_ws)
                            self.log(f"✅ Connected to fresh browser profile at {found_ws}", "SUCCESS")
                        else:
                            self.log("⚠️ No active browser profile detected after waiting. Operating on active window.", "WARNING")

                time.sleep(0.5)

                # PHASE 3: Navigation & Dynamic Event Interpolation
                if target_url and getattr(self.cdp, 'ws_url', None):
                    try:
                        self.log(f"Navigating to {target_url} in browser profile...")
                        self.cdp.navigate(target_url)
                        time.sleep(1.5)
                        try:
                            self.cdp.bring_to_front()
                        except Exception:
                            pass
                    except Exception as nav_err:
                        self.log(f"CDP Navigation warning ({nav_err}). Continuing on active page...", "WARNING")
                elif target_url:
                    self.log("Browser profile not connected via CDP. Operating on active window.", "INFO")

                # Clone template and interpolate variables
                events = copy.deepcopy(template_events)
                for ev in events:
                    if ev.text and "{{" in ev.text:
                        for k, v in raw_data.items():
                            if v is not None:
                                ev.text = ev.text.replace(f"{{{{{k}}}}}", str(v))

                self.log("Executing Form-Fill Actions...")
                self.player.load_events(events)
                self.player.play(loops=1, auto_csv_loops=False)

                while self.player.is_playing() and not self._stop_requested:
                    time.sleep(0.3)

                if self._stop_requested:
                    self.log("Operation stopped by user.")
                    break

                had_playback_issue = self.player._stop_requested
                if had_playback_issue:
                    if not semi_automated:
                        self.log(f"Row {display_row} aborted prematurely. [ERROR]")
                        self.excel.mark_row_status(internal_idx, "Status", "❌ ABORTED")
                        curr_row += 1
                        continue
                    else:
                        self.log(f"⚠️ Row {display_row} encountered a step issue. Pausing for your review... Please check page and click 'Mark Done & Next (F9)' to continue.", "WARNING")

                # PHASE 4: Semi-Automated Pause & Manual Intervention
                if semi_automated:
                    self._is_waiting_manual = True
                    self._manual_resume_event.clear()
                    self._notify_state("WAITING_MANUAL", display_row, end_row)

                    # Audio Chime
                    if winsound:
                        try:
                            winsound.MessageBeep(winsound.MB_ICONASTERISK)
                        except Exception:
                            pass

                    self.log(f"🔔 Row {display_row} filled! Waiting for manual check (QR / Checkbox)... Hit F9 or click 'Done' to continue.")

                    if self.on_waiting_manual_step:
                        try:
                            self.on_waiting_manual_step(display_row)
                        except Exception:
                            pass

                    # Block until user hits Done (F9) or Stop
                    self._manual_resume_event.wait()
                    self._is_waiting_manual = False

                    if self._stop_requested:
                        self.log(f"Row {display_row} stopped during manual step.")
                        self.excel.mark_row_status(internal_idx, "Status", "❌ STOPPED")
                        break

                    conf_word = self._current_conf_word or "Polash"
                    action = self._current_action or "➡️ Move to Next Row"
                else:
                    conf_word = self._current_conf_word or "DONE"
                    action = self._current_action or "➡️ Move to Next Row"

                # PHASE 5: Persist Row Status Tag
                self.log(f"Row {display_row} marked as '{conf_word}'. Saving to disk...")
                self.excel.mark_row_status(internal_idx, "Status", conf_word)

                # Save Progress State
                csv_path = getattr(self.excel, 'filepath', None)
                if csv_path:
                    csv_name = os.path.basename(csv_path)
                    sm = SettingsManager()
                    sm.config.setdefault("csv_states", {})[csv_name] = display_row + 1
                    sm.save()

                # PHASE 6: Handle Completion Action
                if "Repeat" in action:
                    self.log(f"Action: Repeating same Row {display_row} on next cycle.")
                    # Keep curr_row the same
                elif "Pause" in action:
                    self.log(f"Action: Pausing before next row. Hit F9 or Resume to begin Row {display_row + 1}.")
                    curr_row += 1
                    if curr_row <= end_row and not self._stop_requested:
                        self._is_waiting_manual = True
                        self._manual_resume_event.clear()
                        self._notify_state("WAITING_MANUAL", curr_row, end_row)
                        self._manual_resume_event.wait()
                        self._is_waiting_manual = False
                        if self._stop_requested:
                            break
                else:
                    # Move to Next Row
                    curr_row += 1

                # Teardown Profile if managed
                if getattr(self, 'auto_launch_profiles', False):
                    self.cdp.disconnect()
                    if SettingsManager().get("nst", "auto_close_profile", True):
                        self.nst.stop_profile()

            except Exception as e:
                err_str = str(e)
                self.log(f"Error on row {display_row}: {err_str}", "ERROR")
                self.excel.mark_row_status(internal_idx, "Status", f"❌ ERROR: {err_str[:40]}")

                try:
                    if getattr(self, 'auto_launch_profiles', False):
                        self.cdp.disconnect()
                except Exception:
                    pass

                # Circuit Breaker: If connection failed/refused, halt immediately!
                err_lower = err_str.lower()
                is_fatal_conn = any(t in err_lower for t in ["econnrefused", "connection refused", "targetclosederror", "cannot connect to cdp"])
                if is_fatal_conn:
                    self.log("🚨 Browser connection disconnected or refused! Halting bulk execution to protect your dataset.", "ERROR")
                    if hasattr(self.cdp, 'disconnect'):
                        self.cdp.disconnect()
                    break

                # Semi-automated error pause: Give the user control instead of skipping rows!
                if semi_automated and not self._stop_requested:
                    self.log(f"⚠️ Row {display_row} encountered an error. Pausing execution. Check page and hit F9 to continue, or click Stop.", "WARNING")
                    self._is_waiting_manual = True
                    self._manual_resume_event.clear()
                    self._notify_state("WAITING_MANUAL", display_row, end_row)
                    self._manual_resume_event.wait()
                    self._is_waiting_manual = False
                    if self._stop_requested:
                        break

                curr_row += 1

        if self._stop_requested:
            self._notify_state("STOPPED")
            self.log("Operation Stopped.")
        else:
            self._notify_state("FINISHED")
            self.log("Operation Finished.")
