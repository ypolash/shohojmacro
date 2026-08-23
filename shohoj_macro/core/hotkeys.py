"""
Global Low-Level Hotkey Manager
Handles system-wide shortcuts (F8: Record/Stop, F9: Play/Pause, F10: Kill Switch)
even when Shohoj Macro is minimized or backgrounded.
"""

from typing import Callable
import threading
from pynput import keyboard


class GlobalHotkeyManager:
    """Manages system-wide hotkeys."""

    def __init__(
        self,
        on_toggle_record: Callable = None,
        on_toggle_play: Callable = None,
        on_emergency_stop: Callable = None,
    ):
        self.on_toggle_record = on_toggle_record
        self.on_toggle_play = on_toggle_play
        self.on_emergency_stop = on_emergency_stop

        self.record_hotkey = "<f8>"
        self.play_hotkey = "<f9>"
        self.stop_hotkey = "<f10>"

        self._listener: keyboard.GlobalHotKeys = None
        self._is_active = False

    def start(self):
        """Starts global hotkey listener thread."""
        if self._is_active:
            return

        hotkey_map = {}
        if self.on_toggle_record:
            hotkey_map[self.record_hotkey] = self.on_toggle_record
        if self.on_toggle_play:
            hotkey_map[self.play_hotkey] = self.on_toggle_play
        if self.on_emergency_stop:
            hotkey_map[self.stop_hotkey] = self.on_emergency_stop

        try:
            self._listener = keyboard.GlobalHotKeys(hotkey_map)
            self._listener.daemon = True
            self._listener.start()
            self._is_active = True
        except Exception as e:
            print(f"Failed to register global hotkeys: {e}")

    def stop(self):
        """Stops global hotkey listener."""
        if self._listener and self._is_active:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._is_active = False

    def update_hotkeys(self, record_key: str, play_key: str, stop_key: str):
        """Rebinds global hotkeys."""
        self.stop()
        self.record_hotkey = record_key
        self.play_hotkey = play_key
        self.stop_hotkey = stop_key
        self.start()
