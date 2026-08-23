"""
Direct Hardware SendInput (ScanCodes), Mouse, Keyboard & Windows 11 DWM Helpers
"""

import ctypes
from ctypes import wintypes
import time
import random
from shohoj_macro.utils.timer import hires_sleep_ms, hires_sleep

user32 = ctypes.windll.user32
dwmapi = getattr(ctypes.windll, "dwmapi", None)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

# Mouse flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000

# Keyboard flags
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# DWM Window Corner Preferences (Windows 11)
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
DWMWCP_ROUNDSMALL = 3


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUTunion),
    ]


def set_dwm_rounded_corners(hwnd: int, round_type: int = DWMWCP_ROUND):
    """Enables native Windows 11 hardware anti-aliased rounded window corners."""
    if dwmapi and hwnd:
        try:
            val = ctypes.c_int(round_type)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(val),
                ctypes.sizeof(val),
            )
        except Exception:
            pass


def get_screen_dimensions() -> tuple[int, int]:
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    return w, h


def get_cursor_pos() -> tuple[int, int]:
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def get_foreground_window_handle() -> int:
    return user32.GetForegroundWindow()


def set_foreground_window(hwnd: int):
    try:
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def map_vk_to_scancode(vk_code: int) -> int:
    """Maps virtual key code to hardware scan code."""
    if not vk_code:
        return 0
    return user32.MapVirtualKeyW(vk_code, 0)


def char_to_vk_and_scan(char: str) -> tuple[int, int, bool]:
    """
    Resolves a Unicode character to (vk_code, scan_code, shift_needed).
    """
    if not char:
        return 0, 0, False
    try:
        user32.VkKeyScanW.argtypes = [wintypes.WCHAR]
        user32.VkKeyScanW.restype = wintypes.SHORT
        code = user32.VkKeyScanW(char[0])
    except Exception:
        code = -1

    if code == -1:
        return 0, 0, False
    vk = code & 0xFF
    shift = bool(code & 0x100)
    scan = user32.MapVirtualKeyW(vk, 0)
    return vk, scan, shift


def send_mouse_move(x: int, y: int):
    """Normalized virtual desktop mouse move."""
    left = user32.GetSystemMetrics(76)
    top = user32.GetSystemMetrics(77)
    width = user32.GetSystemMetrics(78)
    height = user32.GetSystemMetrics(79)

    norm_x = int((x - left) * (65535.0 / max(1, width - 1)))
    norm_y = int((y - top) * (65535.0 / max(1, height - 1)))

    extra = ctypes.c_ulong(0)
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dx = norm_x
    inp.union.mi.dy = norm_y
    inp.union.mi.mouseData = 0
    inp.union.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = ctypes.pointer(extra)

    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_mouse_down(button: str = "left", x: int = None, y: int = None):
    if x is not None and y is not None:
        send_mouse_move(x, y)

    flags = MOUSEEVENTF_LEFTDOWN
    if button == "right":
        flags = MOUSEEVENTF_RIGHTDOWN
    elif button == "middle":
        flags = MOUSEEVENTF_MIDDLEDOWN

    extra = ctypes.c_ulong(0)
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dwFlags = flags
    inp.union.mi.dwExtraInfo = ctypes.pointer(extra)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_mouse_up(button: str = "left", x: int = None, y: int = None):
    if x is not None and y is not None:
        send_mouse_move(x, y)

    flags = MOUSEEVENTF_LEFTUP
    if button == "right":
        flags = MOUSEEVENTF_RIGHTUP
    elif button == "middle":
        flags = MOUSEEVENTF_MIDDLEUP

    extra = ctypes.c_ulong(0)
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dwFlags = flags
    inp.union.mi.dwExtraInfo = ctypes.pointer(extra)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_mouse_click(button: str = "left", x: int = None, y: int = None, hold_ms: float = 40.0):
    send_mouse_down(button, x, y)
    if hold_ms > 0:
        hires_sleep_ms(hold_ms)
    send_mouse_up(button, x, y)


def send_mouse_scroll(dy: int = 0, dx: int = 0):
    extra = ctypes.c_ulong(0)
    if dy != 0:
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.mouseData = dy * 120
        inp.union.mi.dwFlags = MOUSEEVENTF_WHEEL
        inp.union.mi.dwExtraInfo = ctypes.pointer(extra)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    if dx != 0:
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.mouseData = dx * 120
        inp.union.mi.dwFlags = MOUSEEVENTF_HWHEEL
        inp.union.mi.dwExtraInfo = ctypes.pointer(extra)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_key_down(vk_code: int = 0, scan_code: int = 0):
    flags = 0
    if not scan_code and vk_code:
        scan_code = map_vk_to_scancode(vk_code)

    if scan_code > 0:
        flags |= KEYEVENTF_SCANCODE

    extra = ctypes.c_ulong(0)
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk_code if not scan_code else 0
    inp.union.ki.wScan = scan_code
    inp.union.ki.dwFlags = flags
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = ctypes.pointer(extra)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_key_up(vk_code: int = 0, scan_code: int = 0):
    flags = KEYEVENTF_KEYUP
    if not scan_code and vk_code:
        scan_code = map_vk_to_scancode(vk_code)

    if scan_code > 0:
        flags |= KEYEVENTF_SCANCODE

    extra = ctypes.c_ulong(0)
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk_code if not scan_code else 0
    inp.union.ki.wScan = scan_code
    inp.union.ki.dwFlags = flags
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = ctypes.pointer(extra)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_key_press(vk_code: int = 0, scan_code: int = 0, hold_ms: float = 35.0):
    send_key_down(vk_code, scan_code)
    if hold_ms > 0:
        hires_sleep_ms(hold_ms)
    send_key_up(vk_code, scan_code)


def send_unicode_char(char: str, hold_ms: float = 30.0):
    """Sends a Unicode character directly using KEYEVENTF_UNICODE."""
    code = ord(char)
    extra = ctypes.c_ulong(0)

    inp_down = INPUT()
    inp_down.type = INPUT_KEYBOARD
    inp_down.union.ki.wVk = 0
    inp_down.union.ki.wScan = code
    inp_down.union.ki.dwFlags = KEYEVENTF_UNICODE
    inp_down.union.ki.dwExtraInfo = ctypes.pointer(extra)

    inp_up = INPUT()
    inp_up.type = INPUT_KEYBOARD
    inp_up.union.ki.wVk = 0
    inp_up.union.ki.wScan = code
    inp_up.union.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
    inp_up.union.ki.dwExtraInfo = ctypes.pointer(extra)

    user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
    if hold_ms > 0:
        hires_sleep_ms(hold_ms)
    user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))


def send_smart_text(text: str, wpm: int = 80, auto_clear_first: bool = False):
    """
    Sends natural human typing with React/Vue SPA controlled input compatibility.
    """
    if auto_clear_first:
        # Ctrl+A -> Backspace
        VK_CONTROL = 0x11
        VK_A = 0x41
        VK_BACK = 0x08
        send_key_down(VK_CONTROL)
        send_key_press(VK_A, hold_ms=25)
        send_key_up(VK_CONTROL)
        hires_sleep(0.04)
        send_key_press(VK_BACK, hold_ms=25)
        hires_sleep(0.06)

    # Calculate average inter-key delay based on WPM (5 chars per word)
    chars_per_sec = (wpm * 5) / 60.0
    avg_delay_sec = 1.0 / max(1.0, chars_per_sec)

    for char in text:
        vk, scan, shift = char_to_vk_and_scan(char)
        if vk and scan:
            if shift:
                send_key_down(0x10)  # Shift down
                hires_sleep(0.02)
            send_key_press(vk_code=vk, scan_code=scan, hold_ms=random.uniform(25, 45))
            if shift:
                hires_sleep(0.01)
                send_key_up(0x10)  # Shift up
        else:
            send_unicode_char(char, hold_ms=random.uniform(25, 45))

        # Gaussian typing rhythm
        jitter = random.gauss(0, avg_delay_sec * 0.25)
        inter_key_sleep = max(0.015, avg_delay_sec + jitter)
        hires_sleep(inter_key_sleep)


def send_text(text: str, wpm: int = 75):
    send_smart_text(text, wpm=wpm, auto_clear_first=False)


def set_input_blocked(block: bool):
    try:
        user32.BlockInput(ctypes.c_bool(block))
    except Exception:
        pass


def get_foreground_window_title() -> str:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value
