"""
Visual & Pixel Color Triggers
Evaluates on-screen pixel color conditions with configurable timeout and tolerance.
"""

import time
from shohoj_macro.utils.color_utils import (
    sample_screen_pixel,
    hex_to_rgb,
    color_matches,
)
from shohoj_macro.utils.timer import hires_sleep


class TriggerEvaluator:
    """Evaluates pixel color checks and dynamic triggers."""

    @staticmethod
    def wait_for_pixel_color(
        x: int,
        y: int,
        target_hex: str,
        tolerance: int = 15,
        timeout_ms: float = 3000.0,
        cancel_check_fn=None,
    ) -> bool:
        """
        Polls pixel at (X, Y) until it matches target_hex within tolerance or times out.
        """
        target_rgb = hex_to_rgb(target_hex)
        start_time = time.perf_counter()
        timeout_sec = timeout_ms / 1000.0

        while time.perf_counter() - start_time < timeout_sec:
            if cancel_check_fn and cancel_check_fn():
                return False

            current_rgb = sample_screen_pixel(x, y)
            if color_matches(current_rgb, target_rgb, tolerance):
                return True

            hires_sleep(0.02)  # 20ms check interval

        return False

    @staticmethod
    def check_pixel_immediate(x: int, y: int, target_hex: str, tolerance: int = 15) -> bool:
        """Instant single-shot pixel check."""
        target_rgb = hex_to_rgb(target_hex)
        current_rgb = sample_screen_pixel(x, y)
        return color_matches(current_rgb, target_rgb, tolerance)
