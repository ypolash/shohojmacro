"""
Direct Win32 Hardware SendInput & Window Management API
Provides low-level hardware scancodes and mouse events to work inside
elevated applications, games, and secure desktops.
"""

import ctypes
from ctypes import wintypes
import time

# Win32 Constants
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

# Keyboard flags
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# Virtual Screen Metrics for absolute mouse positioning
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

# Ctypes Structure Definitions
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUT_UNION),
    ]


user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT


def _to_normalized_coords(x: int, y: int) -> tuple[int, int]:
    """Converts screen pixel coordinates to Win32 normalized absolute coordinates (0..65535)."""
    v_left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    v_top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    v_width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    v_height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)

    if v_width <= 0:
        v_width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
    if v_height <= 0:
        v_height = user32.GetSystemMetrics(1)  # SM_CYSCREEN

    norm_x = int(((x - v_left) * 65536) / v_width)
    norm_y = int(((y - v_top) * 65536) / v_height)
    return norm_x, norm_y


def get_cursor_pos() -> tuple[int, int]:
    """Returns current mouse cursor (X, Y) coordinates."""
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


def send_mouse_move(x: int, y: int):
    """Instantly positions cursor at (X, Y) using Win32 SendInput absolute coordinates."""
    norm_x, norm_y = _to_normalized_coords(x, y)
    inp = INPUT(
        type=INPUT_MOUSE,
        u=_INPUT_UNION(
            mi=MOUSEINPUT(
                dx=norm_x,
                dy=norm_y,
                mouseData=0,
                dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | 0x4000,  # MOUSEEVENTF_VIRTUALDESK
                time=0,
                dwExtraInfo=0,
            )
        ),
    )
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_mouse_down(button: str = "left", x: int = None, y: int = None):
    """Sends MouseDown event."""
    if x is not None and y is not None:
        send_mouse_move(x, y)

    btn_flag = MOUSEEVENTF_LEFTDOWN
    if button == "right":
        btn_flag = MOUSEEVENTF_RIGHTDOWN
    elif button == "middle":
        btn_flag = MOUSEEVENTF_MIDDLEDOWN

    inp = INPUT(
        type=INPUT_MOUSE,
        u=_INPUT_UNION(
            mi=MOUSEINPUT(
                dx=0, dy=0, mouseData=0, dwFlags=btn_flag, time=0, dwExtraInfo=0
            )
        ),
    )
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_mouse_up(button: str = "left", x: int = None, y: int = None):
    """Sends MouseUp event."""
    if x is not None and y is not None:
        send_mouse_move(x, y)

    btn_flag = MOUSEEVENTF_LEFTUP
    if button == "right":
        btn_flag = MOUSEEVENTF_RIGHTUP
    elif button == "middle":
        btn_flag = MOUSEEVENTF_MIDDLEUP

    inp = INPUT(
        type=INPUT_MOUSE,
        u=_INPUT_UNION(
            mi=MOUSEINPUT(
                dx=0, dy=0, mouseData=0, dwFlags=btn_flag, time=0, dwExtraInfo=0
            )
        ),
    )
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_mouse_click(button: str = "left", x: int = None, y: int = None, hold_ms: float = 65.0):
    """Sends a complete humanized click (down -> hold -> up)."""
    send_mouse_down(button, x, y)
    if hold_ms > 0:
        time.sleep(hold_ms / 1000.0)
    send_mouse_up(button)


def send_mouse_scroll(dy: int = 0, dx: int = 0):
    """
    Sends vertical and horizontal mouse scroll deltas.
    1 notch is standard WHEEL_DELTA (120).
    """
    if dy != 0:
        inp_v = INPUT(
            type=INPUT_MOUSE,
            u=_INPUT_UNION(
                mi=MOUSEINPUT(
                    dx=0,
                    dy=0,
                    mouseData=int(dy * 120),
                    dwFlags=MOUSEEVENTF_WHEEL,
                    time=0,
                    dwExtraInfo=0,
                )
            ),
        )
        user32.SendInput(1, ctypes.byref(inp_v), ctypes.sizeof(INPUT))

    if dx != 0:
        inp_h = INPUT(
            type=INPUT_MOUSE,
            u=_INPUT_UNION(
                mi=MOUSEINPUT(
                    dx=0,
                    dy=0,
                    mouseData=int(dx * 120),
                    dwFlags=MOUSEEVENTF_HWHEEL,
                    time=0,
                    dwExtraInfo=0,
                )
            ),
        )
        user32.SendInput(1, ctypes.byref(inp_h), ctypes.sizeof(INPUT))


def send_key_down(vk_code: int = 0, scan_code: int = 0):
    """Sends KeyDown with hardware scancode or virtual key."""
    flags = 0
    if scan_code > 0:
        flags |= KEYEVENTF_SCANCODE
        if scan_code > 0xFF:
            flags |= KEYEVENTF_EXTENDEDKEY

    inp = INPUT(
        type=INPUT_KEYBOARD,
        u=_INPUT_UNION(
            ki=KEYBDINPUT(
                wVk=vk_code,
                wScan=scan_code,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0,
            )
        ),
    )
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_key_up(vk_code: int = 0, scan_code: int = 0):
    """Sends KeyUp with hardware scancode or virtual key."""
    flags = KEYEVENTF_KEYUP
    if scan_code > 0:
        flags |= KEYEVENTF_SCANCODE
        if scan_code > 0xFF:
            flags |= KEYEVENTF_EXTENDEDKEY

    inp = INPUT(
        type=INPUT_KEYBOARD,
        u=_INPUT_UNION(
            ki=KEYBDINPUT(
                wVk=vk_code,
                wScan=scan_code,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0,
            )
        ),
    )
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_key_press(vk_code: int = 0, scan_code: int = 0, hold_ms: float = 35.0):
    """Sends full KeyPress (Down -> Hold -> Up)."""
    send_key_down(vk_code, scan_code)
    if hold_ms > 0:
        time.sleep(hold_ms / 1000.0)
    send_key_up(vk_code, scan_code)


def send_unicode_char(char: str):
    """Sends a Unicode character directly using KEYEVENTF_UNICODE."""
    code = ord(char)
    inp_down = INPUT(
        type=INPUT_KEYBOARD,
        u=_INPUT_UNION(
            ki=KEYBDINPUT(
                wVk=0,
                wScan=code,
                dwFlags=KEYEVENTF_UNICODE,
                time=0,
                dwExtraInfo=0,
            )
        ),
    )
    inp_up = INPUT(
        type=INPUT_KEYBOARD,
        u=_INPUT_UNION(
            ki=KEYBDINPUT(
                wVk=0,
                wScan=code,
                dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                time=0,
                dwExtraInfo=0,
            )
        ),
    )
    user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
    user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))


def send_text(text: str, wpm: int = 75, human_variance_ms: float = 20.0):
    """Types out a complete text string with humanized cadence."""
    import random
    base_delay = 60.0 / (wpm * 5.0)  # average delay per character in seconds

    for char in text:
        send_unicode_char(char)
        jitter = random.uniform(-human_variance_ms / 1000.0, human_variance_ms / 1000.0)
        delay = max(0.015, base_delay + jitter)
        time.sleep(delay)


def get_foreground_window_handle() -> int:
    """Returns handle (HWND) of the current foreground active window."""
    return user32.GetForegroundWindow()


def get_foreground_window_title() -> str:
    """Returns title text of the current foreground active window."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value


def set_foreground_window(hwnd: int) -> bool:
    """Brings the specified window handle to the foreground."""
    if not hwnd:
        return False
    try:
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def set_input_blocked(block: bool) -> bool:
    """
    Blocks or unblocks physical mouse/keyboard input from interfering with macro.
    (Ctrl+Alt+Del always unlocks the OS).
    """
    try:
        return bool(user32.BlockInput(ctypes.c_bool(block)))
    except Exception:
        return False
