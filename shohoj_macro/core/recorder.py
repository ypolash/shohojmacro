"""
High-Precision Input Recorder with RDP Path Compression & Hotkey Suppression
Captures low-level mouse and keyboard events with configurable noise filters and modes.
"""

import time
import threading
from typing import Callable
from pynput import mouse, keyboard
from shohoj_macro.core.events import MacroEvent, EventType
from shohoj_macro.utils.path_simplify import rdp_simplify


class MacroRecorder:
    """Records global input events with configurable noise filters and hotkey exclusion."""

    def __init__(self, on_event_recorded: Callable[[MacroEvent], None] = None):
        self.on_event_recorded = on_event_recorded
        self.is_recording = False
        self.recording_mode = "ALL"  # "ALL", "CLICKS_AND_KEYS", "KEYS_ONLY"
        self.path_compression_epsilon = 2.5
        self.max_idle_delay_ms = 1500.0  # Cap idle pauses to 1.5s max

        # Set of hotkeys to suppress from recording
        self.ignored_keys = {"f8", "f9", "f10", "esc", "pause"}

        self._recorded_events: list[MacroEvent] = []
        self._last_event_time = 0.0
        self._mouse_listener = None
        self._keyboard_listener = None
        self._pending_move_points: list[tuple[int, int]] = []
        self._move_lock = threading.Lock()

    def set_ignored_keys(self, keys: list[str]):
        """Sets custom hotkey strings to ignore from recording."""
        self.ignored_keys = {k.strip("<>").lower() for k in keys}
        self.ignored_keys.update({"f8", "f9", "f10", "esc"})

    def start(self, mode: str = "ALL"):
        """Starts global hook capture."""
        if self.is_recording:
            return

        self._recorded_events.clear()
        self._pending_move_points.clear()
        self.recording_mode = mode
        self.is_recording = True
        self._last_event_time = time.perf_counter()

        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )

        self._mouse_listener.daemon = True
        self._keyboard_listener.daemon = True
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop(self) -> list[MacroEvent]:
        """Stops recording, flushes pending move trails, and returns events."""
        if not self.is_recording:
            return self._recorded_events

        self.is_recording = False
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass

        self._flush_pending_moves()
        return list(self._recorded_events)

    def _get_time_delta_ms(self) -> float:
        now = time.perf_counter()
        delta = (now - self._last_event_time) * 1000.0
        self._last_event_time = now
        # Apply idle pause cap
        capped = min(self.max_idle_delay_ms, max(15.0, delta))
        return capped

    def _flush_pending_moves(self):
        with self._move_lock:
            if not self._pending_move_points or self.recording_mode != "ALL":
                self._pending_move_points.clear()
                return

            if len(self._pending_move_points) == 1:
                pt = self._pending_move_points[0]
                ev = MacroEvent(
                    event_type=EventType.MOUSE_MOVE,
                    x=pt[0],
                    y=pt[1],
                    curve_type="windmouse",
                    delay_after_ms=self._get_time_delta_ms(),
                )
                self._emit_event(ev)
            else:
                simplified = rdp_simplify(self._pending_move_points, epsilon=self.path_compression_epsilon)
                for pt in simplified:
                    ev = MacroEvent(
                        event_type=EventType.MOUSE_MOVE,
                        x=int(pt[0]),
                        y=int(pt[1]),
                        curve_type="windmouse",
                        delay_after_ms=18.0,
                    )
                    self._emit_event(ev)

            self._pending_move_points.clear()

    def _emit_event(self, ev: MacroEvent):
        self._recorded_events.append(ev)
        if self.on_event_recorded:
            self.on_event_recorded(ev)

    def _on_mouse_move(self, x, y):
        if not self.is_recording or self.recording_mode != "ALL":
            return
        with self._move_lock:
            self._pending_move_points.append((int(x), int(y)))

    def _on_mouse_click(self, x, y, button, pressed):
        if not self.is_recording or self.recording_mode == "KEYS_ONLY":
            return

        self._flush_pending_moves()

        btn_str = "left"
        if button == mouse.Button.right:
            btn_str = "right"
        elif button == mouse.Button.middle:
            btn_str = "middle"

        if pressed:
            ev = MacroEvent(
                event_type=EventType.MOUSE_DOWN,
                x=int(x),
                y=int(y),
                button=btn_str,
                delay_after_ms=self._get_time_delta_ms(),
            )
            self._emit_event(ev)
        else:
            # Merge Down + Up into single Click if within 300ms
            if (
                self._recorded_events
                and self._recorded_events[-1].event_type == EventType.MOUSE_DOWN
                and self._recorded_events[-1].button == btn_str
                and abs(self._recorded_events[-1].x - int(x)) <= 4
                and abs(self._recorded_events[-1].y - int(y)) <= 4
            ):
                prev_down = self._recorded_events.pop()
                click_ev = MacroEvent(
                    event_type=EventType.MOUSE_CLICK,
                    x=int(x),
                    y=int(y),
                    button=btn_str,
                    click_count=1,
                    delay_after_ms=self._get_time_delta_ms(),
                )
                self._emit_event(click_ev)
            else:
                ev = MacroEvent(
                    event_type=EventType.MOUSE_UP,
                    x=int(x),
                    y=int(y),
                    button=btn_str,
                    delay_after_ms=self._get_time_delta_ms(),
                )
                self._emit_event(ev)

    def _on_mouse_scroll(self, x, y, dx, dy):
        if not self.is_recording or self.recording_mode == "KEYS_ONLY":
            return

        self._flush_pending_moves()
        ev = MacroEvent(
            event_type=EventType.MOUSE_SCROLL,
            x=int(x),
            y=int(y),
            scroll_dy=int(dy),
            scroll_dx=int(dx),
            delay_after_ms=self._get_time_delta_ms(),
        )
        self._emit_event(ev)

    def _on_key_press(self, key):
        if not self.is_recording:
            return

        key_name = self._format_key_name(key)
        # Suppress control hotkeys like F8, F9, F10
        if key_name.lower() in self.ignored_keys:
            return

        self._flush_pending_moves()
        vk = getattr(key, "vk", 0) or 0

        ev = MacroEvent(
            event_type=EventType.KEY_DOWN,
            key_name=key_name,
            vk_code=vk,
            delay_after_ms=self._get_time_delta_ms(),
        )
        self._emit_event(ev)

    def _on_key_release(self, key):
        if not self.is_recording:
            return

        key_name = self._format_key_name(key)
        # Suppress control hotkeys
        if key_name.lower() in self.ignored_keys:
            return

        self._flush_pending_moves()
        vk = getattr(key, "vk", 0) or 0

        # Merge Down + Up into KeyPress
        if (
            self._recorded_events
            and self._recorded_events[-1].event_type == EventType.KEY_DOWN
            and self._recorded_events[-1].key_name == key_name
        ):
            prev_down = self._recorded_events.pop()
            press_ev = MacroEvent(
                event_type=EventType.KEY_PRESS,
                key_name=key_name,
                vk_code=vk,
                delay_after_ms=self._get_time_delta_ms(),
            )
            self._emit_event(press_ev)
        else:
            ev = MacroEvent(
                event_type=EventType.KEY_UP,
                key_name=key_name,
                vk_code=vk,
                delay_after_ms=self._get_time_delta_ms(),
            )
            self._emit_event(ev)

    def _format_key_name(self, key) -> str:
        try:
            return key.char if hasattr(key, "char") and key.char else key.name
        except Exception:
            return str(key).replace("Key.", "")
