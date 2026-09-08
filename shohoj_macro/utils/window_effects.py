import ctypes
import sys

def apply_mica(hwnd, dark_mode=True):
    """
    Applies True Windows 11 Mica / Acrylic blur to a window if supported.
    hwnd: Window handle (e.g. root.winfo_id())
    dark_mode: Whether to apply the immersive dark mode blur
    """
    if sys.platform != "win32":
        return

    try:
        # Windows 11 Build 22000+ DWMWA constants
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        
        # 1 = Auto, 2 = Mica, 3 = Acrylic, 4 = Mica Alt
        backdrop_type = 2 

        # Set Dark Mode
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 
            DWMWA_USE_IMMERSIVE_DARK_MODE, 
            ctypes.byref(ctypes.c_int(1 if dark_mode else 0)), 
            ctypes.sizeof(ctypes.c_int)
        )
        
        # Set Mica Backdrop
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 
            DWMWA_SYSTEMBACKDROP_TYPE, 
            ctypes.byref(ctypes.c_int(backdrop_type)),
            ctypes.sizeof(ctypes.c_int)
        )
    except Exception:
        pass
