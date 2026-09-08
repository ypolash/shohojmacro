"""
High-Precision Playback Engine with Visual Frame Synchronization & CSV Data Injection (v2.0.0 Enterprise)
Executes AST event sequences with sub-millisecond precision, auto-adjusting image anchors, and CSV iteration.
"""

import time
import threading
import random
import math
from typing import Callable, Optional
from shohoj_macro.core.events import MacroEvent, EventType, ErrorPolicy
from shohoj_macro.core.humanizer import HumanizerEngine
from shohoj_macro.core.stealth_core import StealthCore
from shohoj_macro.core.bio_rhythm import BioRhythmEngine
from shohoj_macro.core.triggers import TriggerEvaluator
from shohoj_macro.core.recaptcha_solver import ReCaptchaSolver
from shohoj_macro.core.window_tracker import WindowTracker
from shohoj_macro.core.cv_engine import CVTemplateMatcher
from shohoj_macro.core.csv_engine import CSVDataEngine
from shohoj_macro.utils.timer import hires_sleep_ms, hires_sleep
from shohoj_macro.utils.win32_input import (
    send_mouse_click,
    send_mouse_down,
    send_mouse_up,
    send_mouse_scroll,
    send_key_down,
    send_key_up,
    send_key_press,
    send_smart_text,
    set_input_blocked,
    get_cursor_pos,
    get_foreground_window_title,
)


class PlaybackState:
    IDLE = "IDLE"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class MacroPlayer:
    """Master playback engine executing macro action trees with CV and CSV engines."""

    def __init__(
        self,
        on_step_started: Callable[[int, MacroEvent], None] = None,
        on_loop_completed: Callable[[int, int], None] = None,
        on_playback_finished: Callable[[bool, str], None] = None,
        on_log_message: Callable[[str, str], None] = None,
        on_supervised_intercept: Callable[[MacroEvent, Callable[[bool], None]], None] = None,
    ):
        self.on_step_started = on_step_started
        self.on_loop_completed = on_loop_completed
        self.on_playback_finished = on_playback_finished
        self.on_log_message = on_log_message
        self.on_supervised_intercept = on_supervised_intercept

        self.state = PlaybackState.IDLE
        self.speed_multiplier = 1.0
        self.total_loops = 1
        self.inter_loop_delay_ms = 100.0
        self.inter_loop_jitter_ms = 0.0
        self.humanizer_enabled = True
        self.bio_rhythm_enabled = True
        self.block_physical_input = False
        self.foreground_lock_title = ""
        self.corner_fail_safe = True
        self.supervised_mode = False

        # Sub-Engines
        self.csv_engine = CSVDataEngine()
        from shohoj_macro.core.cdp_spatial_bridge import CDPSpatialBridge
        from shohoj_macro.core.nst_controller import NSTController
        from shohoj_macro.core.settings_manager import SettingsManager
        self.cdp_bridge = CDPSpatialBridge()
        nst_api_key = SettingsManager().get("nst", "api_key", "")
        self.nst_controller = NSTController(api_key=nst_api_key)
        self._events: list[MacroEvent] = []
        self._thread: Optional[threading.Thread] = None
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_requested = False
        self._bio_rhythm = BioRhythmEngine()

    def load_events(self, events: list[MacroEvent]):
        self._events = list(events)

    def play(self, events: list[MacroEvent] = None, loops: int = 1, speed: float = 1.0, auto_csv_loops: bool = False):
        """Starts asynchronous macro playback."""
        if self.state == PlaybackState.PLAYING:
            return

        if events is not None:
            self._events = list(events)

        if not self._events:
            if self.on_log_message:
                self.on_log_message("No actions in timeline to play.", "WARN")
            return

        # Only auto-expand loops to CSV row count if explicitly requested (e.g. from Builder Studio)
        if auto_csv_loops and self.csv_engine.is_loaded and self.csv_engine.get_row_count() > 1:
            self.total_loops = self.csv_engine.get_row_count()
        else:
            self.total_loops = loops

        self.speed_multiplier = max(0.1, min(20.0, speed))
        self._stop_requested = False
        self._pause_event.set()
        self.state = PlaybackState.PLAYING
        self._bio_rhythm.reset_session()

        self._thread = threading.Thread(target=self._run_playback, daemon=True)
        self._thread.start()

    def pause(self):
        if self.state == PlaybackState.PLAYING:
            self.state = PlaybackState.PAUSED
            self._pause_event.clear()
            if self.on_log_message:
                self.on_log_message("Playback paused.", "INFO")

    def resume(self):
        if self.state == PlaybackState.PAUSED:
            self.state = PlaybackState.PLAYING
            self._pause_event.set()
            if self.on_log_message:
                self.on_log_message("Playback resumed.", "INFO")

    def stop(self):
        self._stop_requested = True
        self._pause_event.set()
        self.state = PlaybackState.STOPPED
        if self.block_physical_input:
            set_input_blocked(False)

    def is_playing(self) -> bool:
        return self.state == PlaybackState.PLAYING

    def is_paused(self) -> bool:
        return self.state == PlaybackState.PAUSED

    def _check_panic_failsafe(self) -> bool:
        """Returns True if user moved mouse to (0, 0) top-left corner."""
        if not self.corner_fail_safe:
            return False
        cx, cy = get_cursor_pos()
        if cx <= 2 and cy <= 2:
            self._stop_requested = True
            if self.on_log_message:
                self.on_log_message("⚠️ Panic Fail-Safe Triggered! (Mouse in top-left corner)", "WARN")
            return True
        return False

    def _run_playback(self):
        success = True
        err_msg = ""
        current_loop = 0

        if self.block_physical_input:
            set_input_blocked(True)

        try:
            while not self._stop_requested:
                current_loop += 1
                row_idx = current_loop - 1  # 0-indexed for CSV

                if self.on_log_message:
                    csv_info = f" [CSV Row {current_loop}/{self.csv_engine.get_row_count()}]" if self.csv_engine.is_loaded else ""
                    loop_str = f"Loop {current_loop}/{self.total_loops}{csv_info}" if self.total_loops > 0 else f"Loop {current_loop} (Infinite)"
                    self.on_log_message(f"--- Starting {loop_str} ---", "INFO")

                step_idx = 0
                while step_idx < len(self._events):
                    if self._stop_requested or self._check_panic_failsafe():
                        break

                    self._pause_event.wait()
                    event = self._events[step_idx]

                    if not event.enabled:
                        step_idx += 1
                        continue

                    # Foreground focus check
                    if self.foreground_lock_title:
                        if not WindowTracker.is_target_window_active(self.foreground_lock_title):
                            if self.on_log_message:
                                self.on_log_message(f"Focus lost! Active: '{get_foreground_window_title()}'. Pausing...", "WARN")
                            self.pause()
                            self._pause_event.wait()

                    if self.on_step_started:
                        self.on_step_started(step_idx, event)

                    step_success = self._execute_event_with_retry(event, row_idx)

                    if not step_success:
                        if event.error_policy == ErrorPolicy.STOP:
                            success = False
                            err_msg = f"Step {step_idx + 1} failed ({event.get_summary()})"
                            self._stop_requested = True
                            break
                        elif event.error_policy == ErrorPolicy.SKIP:
                            if self.on_log_message:
                                self.on_log_message(f"Skipping failed step {step_idx + 1}.", "WARN")

                    # Handle Delay After
                    effective_speed = self.speed_multiplier * self._bio_rhythm.get_speed_multiplier()
                    if event.delay_after_ms > 0:
                        delay_sec = (event.delay_after_ms / 1000.0) / effective_speed
                        hires_sleep(delay_sec)

                    # Bio-rhythm micro-hesitation
                    if self.bio_rhythm_enabled and self._bio_rhythm.should_inject_micro_hesitation():
                        hesitation_sec = self._bio_rhythm.get_micro_hesitation_duration_sec()
                        hires_sleep(hesitation_sec)

                    step_idx += 1

                self._bio_rhythm.on_loop_completed()
                if self.on_loop_completed:
                    self.on_loop_completed(current_loop, self.total_loops)

                if self.total_loops > 0 and current_loop >= self.total_loops:
                    break

                if not self._stop_requested and self.inter_loop_delay_ms > 0:
                    jitter = random.uniform(-self.inter_loop_jitter_ms, self.inter_loop_jitter_ms)
                    rest_sec = max(0.01, (self.inter_loop_delay_ms + jitter) / 1000.0)
                    hires_sleep(rest_sec)

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            success = False
            err_msg = f"{e}\n{tb}"
            if self.on_log_message:
                self.on_log_message(f"Playback exception: {e}\n{tb}", "ERROR")
        finally:
            if self.block_physical_input:
                set_input_blocked(False)
            self.state = PlaybackState.IDLE
            if self.on_playback_finished:
                self.on_playback_finished(success, err_msg)

    def _execute_event_with_retry(self, event: MacroEvent, row_idx: int) -> bool:
        max_attempts = 3 if event.error_policy == ErrorPolicy.RETRY_3 else 1
        for attempt in range(max_attempts):
            try:
                self._execute_single_event(event, row_idx)
                return True
            except Exception as e:
                # If step is configured to SKIP, do not wake Idle Guardian or fail loop
                if event.error_policy == ErrorPolicy.SKIP or "Optional element" in str(e):
                    if self.on_log_message:
                        self.on_log_message(f"Optional step skipped: {e}", "INFO")
                    return True

                # Idle Guardian / Self-Heal Hook for CDP Input Failures
                if "CDP Element" in str(e) and "not found" in str(e):
                    if self.on_log_message:
                        self.on_log_message(f"⚠️ Element '{event.selector}' missing! Waking Idle Guardian...", "WARN")

                    healed = self._self_heal(event, row_idx)
                    if healed:
                        return True # Healing succeeded, step complete

                if attempt < max_attempts - 1:
                    time.sleep(0.15)
                else:
                    if self.on_log_message:
                        self.on_log_message(f"Action error: {e}", "ERROR")
                    return False
        return False
        
    def _self_heal(self, event: MacroEvent, row_idx: int) -> bool:
        """
        The Idle Guardian's core fallback method.
        Called when a CDP physical selector fails to find the element.
        """
        if not self.cdp_bridge._connected:
            return False
            
        # 1. Wait for network idle to ensure the page is actually done loading
        self.cdp_bridge.wait_for_idle(timeout_ms=5000)
        
        # 2. Re-check just in case the wait fixed it
        rect = self.cdp_bridge.get_element_rect(event.selector)
        if rect:
            if self.on_log_message:
                self.on_log_message("Network wait resolved the issue. Proceeding.", "SUCCESS")
            try:
                self._execute_single_event(event, row_idx) # Try again
                return True
            except:
                pass
                
        # 3. True Failure -> Invoke Vision AI
        if self.on_log_message:
            self.on_log_message("Taking viewport screenshot for Vision AI...", "INFO")
            
        try:
            # Capture compressed WebP to save Vision tokens (stateless)
            screenshot_bytes = None
            if self.cdp_bridge.ws_url:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    b = p.chromium.connect_over_cdp(self.cdp_bridge.ws_url)
                    try:
                        c = b.contexts[0] if b.contexts else b.new_context()
                        v = [pg for pg in c.pages if not pg.url.startswith("chrome-extension://")]
                        pg = v[-1] if v else c.new_page()
                        screenshot_bytes = pg.screenshot(type="jpeg", quality=60)
                    finally:
                        b.close()
            
            # TODO (Phase 4): Send to OpenRouterClient to ask for new physical coordinates/selector
            # For now, we scaffold the hook and pause.
            self.pause()
            if self.on_log_message:
                self.on_log_message("Idle Guardian self-healing is scaffolded. Pausing operation for manual intervention.", "WARN")
            return False
            
        except Exception as e:
            if self.on_log_message:
                self.on_log_message(f"Failed to capture screenshot for AI: {e}", "ERROR")
            return False

    def _execute_single_event(self, event: MacroEvent, row_idx: int):
        effective_speed = self.speed_multiplier * self._bio_rhythm.get_speed_multiplier()
        t = event.event_type

        if t == EventType.MOUSE_MOVE:
            if self.humanizer_enabled and event.curve_type != "instant":
                HumanizerEngine.move_humanized(
                    event.x,
                    event.y,
                    duration_ms=event.duration_ms / effective_speed,
                    curve_type=event.curve_type,
                    cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe(),
                )
            else:
                from shohoj_macro.utils.win32_input import send_mouse_move
                send_mouse_move(event.x, event.y)

        elif t == EventType.MOUSE_CLICK:
            target_x = event.x
            target_y = event.y
            if self.humanizer_enabled and event.human_target_radius > 0:
                target_x, target_y = HumanizerEngine.sample_gaussian_point_in_circle(
                    event.x, event.y, event.human_target_radius
                )

            cur_x, cur_y = get_cursor_pos()
            if math.hypot(target_x - cur_x, target_y - cur_y) > 3.0:
                if self.humanizer_enabled:
                    HumanizerEngine.move_humanized(
                        target_x, target_y, duration_ms=120.0 / effective_speed, curve_type="windmouse", cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe()
                    )
                else:
                    from shohoj_macro.utils.win32_input import send_mouse_move
                    send_mouse_move(target_x, target_y)

            hold_ms = StealthCore.calculate_human_click_hold_ms() if self.humanizer_enabled else 45.0
            send_mouse_click(event.button, hold_ms=hold_ms)
            if event.click_count == 2:
                time.sleep(0.08)
                send_mouse_click(event.button, hold_ms=hold_ms)

        elif t == EventType.VISUAL_ANCHOR_CLICK:
            # 1. Decode template image from base64
            if not event.template_base64:
                raise ValueError(f"Visual anchor '{event.template_name}' has no template image.")

            template_bgr = CVTemplateMatcher.decode_base64_to_image(event.template_base64)
            roi = tuple(event.search_roi) if event.search_roi else None

            # 2. Wait / Search for template on screen
            result = CVTemplateMatcher.wait_for_frame_state(
                template_bgr=template_bgr,
                should_exist=True,
                search_roi=roi,
                confidence_threshold=event.confidence_threshold,
                timeout_sec=event.timeout_ms / 1000.0,
                cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe(),
            )

            if not result.found:
                raise TimeoutError(f"Visual Anchor '{event.template_name}' not found (Confidence: {result.confidence*100:.1f}%)")

            # 3. Dynamic Self-Adjustment: Click center of found match
            target_x = result.center_x + event.click_offset_x
            target_y = result.center_y + event.click_offset_y

            if self.humanizer_enabled and event.human_target_radius > 0:
                target_x, target_y = HumanizerEngine.sample_gaussian_point_in_circle(
                    target_x, target_y, event.human_target_radius
                )

            if self.humanizer_enabled:
                HumanizerEngine.move_humanized(
                    target_x, target_y, duration_ms=130.0 / effective_speed, curve_type="windmouse", cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe()
                )
            else:
                from shohoj_macro.utils.win32_input import send_mouse_move
                send_mouse_move(target_x, target_y)

            hold_ms = StealthCore.calculate_human_click_hold_ms() if self.humanizer_enabled else 45.0
            send_mouse_click(event.button, hold_ms=hold_ms)
            if self.on_log_message:
                self.on_log_message(f"🎯 Auto-Adjusted Click on '{event.template_name}' at ({target_x}, {target_y}) [Match: {result.confidence*100:.1f}%]", "SUCCESS")

        elif t == EventType.WAIT_UNTIL_FRAME_APPEARS:
            if not event.template_base64:
                raise ValueError(f"Wait frame '{event.template_name}' has no template image.")

            template_bgr = CVTemplateMatcher.decode_base64_to_image(event.template_base64)
            roi = tuple(event.search_roi) if event.search_roi else None

            result = CVTemplateMatcher.wait_for_frame_state(
                template_bgr=template_bgr,
                should_exist=True,
                search_roi=roi,
                confidence_threshold=event.confidence_threshold,
                timeout_sec=event.timeout_ms / 1000.0,
                cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe(),
            )
            if not result.found:
                raise TimeoutError(f"Frame '{event.template_name}' did not appear within {int(event.timeout_ms/1000)}s.")
            if self.on_log_message:
                self.on_log_message(f"✅ Frame '{event.template_name}' detected on screen [Match: {result.confidence*100:.1f}%]", "SUCCESS")

        elif t == EventType.WAIT_UNTIL_FRAME_DISAPPEARS:
            if not event.template_base64:
                raise ValueError(f"Wait frame '{event.template_name}' has no template image.")

            template_bgr = CVTemplateMatcher.decode_base64_to_image(event.template_base64)
            roi = tuple(event.search_roi) if event.search_roi else None

            result = CVTemplateMatcher.wait_for_frame_state(
                template_bgr=template_bgr,
                should_exist=False,
                search_roi=roi,
                confidence_threshold=event.confidence_threshold,
                timeout_sec=event.timeout_ms / 1000.0,
                cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe(),
            )
            if result.found:
                raise TimeoutError(f"Frame '{event.template_name}' still present after {int(event.timeout_ms/1000)}s.")
            if self.on_log_message:
                self.on_log_message(f"✅ Frame '{event.template_name}' vanished from screen.", "SUCCESS")

        elif t == EventType.MOUSE_DOWN:
            send_mouse_down(event.button, event.x, event.y)

        elif t == EventType.MOUSE_UP:
            send_mouse_up(event.button, event.x, event.y)

        elif t == EventType.MOUSE_DRAG:
            from shohoj_macro.utils.win32_input import send_mouse_move
            send_mouse_move(event.x, event.y)
            send_mouse_down(event.button)
            time.sleep(0.04)
            HumanizerEngine.move_humanized(
                event.end_x, event.end_y, duration_ms=event.duration_ms / effective_speed, curve_type="bezier", cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe()
            )
            time.sleep(0.04)
            send_mouse_up(event.button)

        elif t == EventType.MOUSE_SCROLL:
            send_mouse_scroll(dy=event.scroll_dy, dx=event.scroll_dx)

        elif t == EventType.KEY_PRESS:
            hold_ms = StealthCore.calculate_human_keypress_hold_ms() if self.humanizer_enabled else 30.0
            send_key_press(event.vk_code, event.scan_code, hold_ms=hold_ms)

        elif t == EventType.KEY_DOWN:
            send_key_down(event.vk_code, event.scan_code)

        elif t == EventType.KEY_UP:
            send_key_up(event.vk_code, event.scan_code)

        elif t == EventType.TEXT_TYPE:
            # Interpolate {{variables}} from CSV row if applicable
            final_text = self.csv_engine.interpolate_text(event.text, row_idx)
            send_smart_text(final_text, wpm=int(event.wpm * effective_speed), auto_clear_first=event.auto_clear_first)

        elif t == EventType.DELAY:
            jitter = random.uniform(-event.jitter_ms, event.jitter_ms) if event.jitter_ms > 0 else 0
            dur_sec = max(0.001, ((event.delay_ms + jitter) / 1000.0) / effective_speed)
            hires_sleep(dur_sec)

        elif t == EventType.HUMAN_WANDER_SLOW:
            HumanizerEngine.perform_slow_organic_wander(
                duration_ms=event.duration_ms / effective_speed,
                speed_profile=event.wander_speed_profile,
                cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe(),
            )

        elif t == EventType.HUMAN_WANDER_ZONE:
            HumanizerEngine.perform_human_wander_zone(
                center_x=event.x,
                center_y=event.y,
                radius=event.zone_radius,
                duration_ms=event.duration_ms / effective_speed,
                return_to_origin=event.return_to_origin,
                cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe(),
            )

        elif t == EventType.HUMAN_SCROLL_PEEK:
            HumanizerEngine.perform_human_scroll_peek(
                scroll_notches=event.scroll_dy,
                peek_duration_ms=event.peek_duration_ms / effective_speed,
                cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe(),
            )
            
        elif t == EventType.CDP_PHYSICAL_INPUT:
            if not self.cdp_bridge._connected:
                raise Exception("CDP Bridge not connected! Did you run NST_PREPARE_PROFILE?")
                
            # Intercept for Supervised Mode
            if self.supervised_mode and self.on_supervised_intercept:
                intercept_event = threading.Event()
                intercept_result = [False]
                
                def _resume_callback(approved: bool):
                    intercept_result[0] = approved
                    intercept_event.set()
                    
                # Highlight the element and ask user
                if self.on_log_message:
                    self.on_log_message(f"Supervised Mode: Intercepting click on '{event.selector}'", "WARN")
                    
                self.on_supervised_intercept(event, _resume_callback)
                intercept_event.wait() # Block this background thread until user clicks Yes/No in GUI
                
                # Bring the browser back to focus after the GUI popup steals it
                try:
                    self.cdp_bridge.bring_to_front()
                    time.sleep(0.2)  # Give Windows OS time to switch focus
                except Exception:
                    pass
                
                if not intercept_result[0]:
                    if self.on_log_message:
                        self.on_log_message("Supervised step rejected by user. Aborting operation.", "ERROR")
                    self._stop_requested = True
                    return
                    
            final_text = self.csv_engine.interpolate_text(event.text, row_idx) if event.text else ""
            policy_val = event.error_policy.value if hasattr(event.error_policy, 'value') else str(event.error_policy)

            # Bring browser to front
            try:
                self.cdp_bridge.bring_to_front()
            except Exception:
                pass

            # Optional visual glide for human stealth
            if self.humanizer_enabled:
                try:
                    rect = self.cdp_bridge.get_element_rect(event.selector)
                    if rect:
                        offset_x, offset_y = self.cdp_bridge.get_window_position()
                        target_x = int(rect['x'] + offset_x + (rect['width'] / 2))
                        target_y = int(rect['y'] + offset_y + (rect['height'] / 2))
                        HumanizerEngine.move_humanized(
                            target_x, target_y, duration_ms=100.0 / effective_speed, curve_type="windmouse",
                            cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe()
                        )
                except Exception:
                    pass

            # Execute High-Precision Direct DOM Action via CDP
            self.cdp_bridge.perform_action(
                selector=event.selector,
                text=final_text,
                error_policy=policy_val
            )

            # Auto-solve reCAPTCHA if we clicked on the reCAPTCHA iframe
            if "iframe" in event.selector and "recaptcha" in event.selector.lower():
                if self.on_log_message:
                    self.on_log_message("Detecting reCAPTCHA challenge... Launching Auto-Solver", "INFO")
                solver = ReCaptchaSolver(self.cdp_bridge)
                result = solver.solve()
                if result:
                    if self.on_log_message:
                        self.on_log_message(f"reCAPTCHA solved successfully! ({result})", "SUCCESS")
                else:
                    if self.on_log_message:
                        self.on_log_message("reCAPTCHA solver failed to find a solution.", "ERROR")
                    self._stop_requested = True

        elif t == EventType.NST_PREPARE_PROFILE:
            final_email = self.csv_engine.interpolate_text(event.text, row_idx)
            ws_url = self.nst_controller.prepare_and_launch(final_email, event.target_value)
            if ws_url:
                self.cdp_bridge.connect(ws_url)
                if self.on_log_message:
                    self.on_log_message(f"✅ CDP Bridge connected to '{final_email}'", "SUCCESS")

        elif t == EventType.PIXEL_CHECK:
            matched = TriggerEvaluator.wait_for_pixel_color(
                event.x,
                event.y,
                event.target_hex_color,
                tolerance=event.color_tolerance,
                timeout_ms=event.timeout_ms,
                cancel_check_fn=lambda: self._stop_requested or self._check_panic_failsafe(),
            )
            if not matched:
                raise TimeoutError(f"Pixel check at ({event.x}, {event.y}) failed to match {event.target_hex_color}")
