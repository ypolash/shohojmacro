"""
Per-Monitor DPI V2 & Multi-Monitor Geometry Helpers
"""

import ctypes
from ctypes import wintypes
import sys

user32 = ctypes.WinDLL("user32", use_last_error=True)
shcore = None

try:
    shcore = ctypes.WinDLL("shcore", use_last_error=True)
except Exception:
    shcore = None


def init_dpi_awareness():
    """Initializes Per-Monitor DPI Awareness V2 for Windows 10/11."""
    if sys.platform != "win32":
        return

    # Try DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 (-4)
    try:
        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
        user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        return
    except Exception:
        pass

    # Fallback to SetProcessDpiAwareness(2)
    if shcore:
        try:
            shcore.SetProcessDpiAwareness(2)
            return
        except Exception:
            pass

    # Legacy fallback
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass


def get_screen_metrics() -> dict:
    """Returns virtual desktop boundaries and resolution."""
    v_left = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
    v_top = user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
    v_width = user32.GetSystemMetrics(78) # SM_CXVIRTUALSCREEN
    v_height = user32.GetSystemMetrics(79)# SM_CYVIRTUALSCREEN

    primary_width = user32.GetSystemMetrics(0) # SM_CXSCREEN
    primary_height = user32.GetSystemMetrics(1)# SM_CYSCREEN

    if v_width <= 0:
        v_width = primary_width
    if v_height <= 0:
        v_height = primary_height

    return {
        "virtual_left": v_left,
        "virtual_top": v_top,
        "virtual_width": v_width,
        "virtual_height": v_height,
        "primary_width": primary_width,
        "primary_height": primary_height,
    }
