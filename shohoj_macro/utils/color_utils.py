"""
Color Conversion, Screen Pixel Sampling & Visual Matchers
"""

import ctypes
from ctypes import wintypes
import math
from PIL import ImageGrab

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts RGB integers (0-255) to hex string (e.g. #FF5500)."""
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Converts hex string (e.g. #FF5500 or FF5500) to RGB tuple (255, 85, 0)."""
    h = hex_str.strip().lstrip("#")
    if len(h) == 3:
        h = "".join([c * 2 for c in h])
    if len(h) != 6:
        return 0, 0, 0
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def sample_screen_pixel(x: int, y: int) -> tuple[int, int, int]:
    """
    Samples pixel color at screen coordinates (X, Y) using Win32 GDI GetPixel for maximum speed (<0.1ms).
    """
    hdc = user32.GetDC(0)
    if not hdc:
        # Fallback to PIL ImageGrab
        try:
            bbox = (x, y, x + 1, y + 1)
            im = ImageGrab.grab(bbox=bbox)
            return im.getpixel((0, 0))[:3]
        except Exception:
            return 0, 0, 0

    try:
        color_ref = gdi32.GetPixel(hdc, int(x), int(y))
        # COLORREF format: 0x00BBGGRR
        r = color_ref & 0xFF
        g = (color_ref >> 8) & 0xFF
        b = (color_ref >> 16) & 0xFF
        return r, g, b
    finally:
        user32.ReleaseDC(0, hdc)


def color_matches(
    rgb1: tuple[int, int, int], rgb2: tuple[int, int, int], tolerance: int = 15
) -> bool:
    """
    Checks if two RGB colors match within Euclidean distance tolerance.
    """
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    dist = math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
    return dist <= tolerance
