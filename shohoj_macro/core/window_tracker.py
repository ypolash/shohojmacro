"""
Window Tracking, Relative Coordinate Translation & Foreground Lock
"""

import ctypes
from ctypes import wintypes
from shohoj_macro.utils.win32_input import (
    get_foreground_window_handle,
    get_foreground_window_title,
    set_foreground_window,
)

user32 = ctypes.WinDLL("user32", use_last_error=True)


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class WindowTracker:
    """Manages active window boundaries and coordinate offsets."""

    @staticmethod
    def get_window_rect(hwnd: int) -> tuple[int, int, int, int]:
        """Returns (left, top, width, height) of the given window handle."""
        if not hwnd:
            return 0, 0, 0, 0
        r = RECT()
        if user32.GetWindowRect(hwnd, ctypes.byref(r)):
            return r.left, r.top, r.right - r.left, r.bottom - r.top
        return 0, 0, 0, 0

    @classmethod
    def get_active_window_info(cls) -> dict:
        hwnd = get_foreground_window_handle()
        title = get_foreground_window_title()
        left, top, w, h = cls.get_window_rect(hwnd)
        return {
            "hwnd": hwnd,
            "title": title,
            "left": left,
            "top": top,
            "width": w,
            "height": h,
        }

    @classmethod
    def screen_to_relative(cls, screen_x: int, screen_y: int, hwnd: int) -> tuple[int, int]:
        """Converts absolute screen coordinates to relative window offset."""
        left, top, _, _ = cls.get_window_rect(hwnd)
        return screen_x - left, screen_y - top

    @classmethod
    def relative_to_screen(cls, rel_x: int, rel_y: int, hwnd: int) -> tuple[int, int]:
        """Converts relative window offset back to absolute screen coordinates."""
        left, top, _, _ = cls.get_window_rect(hwnd)
        return left + rel_x, top + rel_y

    @classmethod
    def is_target_window_active(cls, expected_title_substring: str) -> bool:
        """Verifies if the current foreground window matches expected title."""
        if not expected_title_substring:
            return True
        current_title = get_foreground_window_title()
        return expected_title_substring.lower() in current_title.lower()
