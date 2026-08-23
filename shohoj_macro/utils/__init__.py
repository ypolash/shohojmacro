"""
Shohoj Macro Utilities Package
"""

from shohoj_macro.utils.timer import PrecisionTimer, hires_sleep
from shohoj_macro.utils.win32_input import (
    send_mouse_move,
    send_mouse_click,
    send_mouse_down,
    send_mouse_up,
    send_mouse_scroll,
    send_key_down,
    send_key_up,
    send_key_press,
    send_unicode_char,
    send_text,
    get_foreground_window_title,
    get_foreground_window_handle,
    set_foreground_window,
    set_input_blocked,
    get_cursor_pos,
)
from shohoj_macro.utils.dpi_helper import init_dpi_awareness, get_screen_metrics
from shohoj_macro.utils.color_utils import (
    sample_screen_pixel,
    rgb_to_hex,
    hex_to_rgb,
    color_matches,
)
from shohoj_macro.utils.path_simplify import rdp_simplify

__all__ = [
    "PrecisionTimer",
    "hires_sleep",
    "send_mouse_move",
    "send_mouse_click",
    "send_mouse_down",
    "send_mouse_up",
    "send_mouse_scroll",
    "send_key_down",
    "send_key_up",
    "send_key_press",
    "send_unicode_char",
    "send_text",
    "get_foreground_window_title",
    "get_foreground_window_handle",
    "set_foreground_window",
    "set_input_blocked",
    "get_cursor_pos",
    "init_dpi_awareness",
    "get_screen_metrics",
    "sample_screen_pixel",
    "rgb_to_hex",
    "hex_to_rgb",
    "color_matches",
    "rdp_simplify",
]
