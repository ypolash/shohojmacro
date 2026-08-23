"""
Shohoj StealthCore Engine
Handles sub-millisecond 250-500Hz mouse streaming, Zero-GC buffer pre-allocation,
and human physiological click hold duration modeling.
"""

import random
import time
import math
import gc
from shohoj_macro.utils.timer import hires_sleep
from shohoj_macro.utils.win32_input import send_mouse_move, send_mouse_down, send_mouse_up


class StealthCore:
    """Core hardware simulation engine for undetectable physical inputs."""

    @staticmethod
    def calculate_human_click_hold_ms(mean_ms: float = 72.0, std_dev: float = 18.0) -> float:
        """
        Generates realistic human muscle hold duration for mouse down -> mouse up.
        Clamped between 42ms and 140ms.
        """
        val = random.gauss(mean_ms, std_dev)
        return max(42.0, min(140.0, val))

    @staticmethod
    def calculate_human_keypress_hold_ms(mean_ms: float = 55.0, std_dev: float = 14.0) -> float:
        """
        Generates realistic human keypress hold duration (Down -> Up).
        Clamped between 30ms and 110ms.
        """
        val = random.gauss(mean_ms, std_dev)
        return max(30.0, min(110.0, val))

    @staticmethod
    def stream_trajectory_points(
        points: list[tuple[int, int]],
        total_duration_ms: float,
        hz_rate: int = 350,
        cancel_check_fn=None,
    ):
        """
        Streams pre-computed trajectory waypoints at 250-500Hz without GC churn.
        :param points: List of (x, y) integer coordinates.
        :param total_duration_ms: Total duration to complete the travel.
        :param hz_rate: Target packet frequency (e.g. 350Hz = ~2.85ms per packet).
        :param cancel_check_fn: Callable returning True if playback was aborted.
        """
        if not points:
            return

        if len(points) == 1:
            send_mouse_move(points[0][0], points[0][1])
            return

        num_points = len(points)
        packet_interval_sec = 1.0 / hz_rate
        total_sec = total_duration_ms / 1000.0

        # Temporarily disable garbage collection during high-speed move
        gc_was_enabled = gc.isenabled()
        if gc_was_enabled:
            gc.disable()

        try:
            start_time = time.perf_counter()
            end_time = start_time + total_sec

            for i in range(num_points):
                if cancel_check_fn and cancel_check_fn():
                    break

                target_time = start_time + (i / float(num_points)) * total_sec
                now = time.perf_counter()
                sleep_needed = target_time - now
                if sleep_needed > 0:
                    hires_sleep(sleep_needed)

                px, py = points[i]
                send_mouse_move(px, py)

            # Ensure final exact landing
            last_x, last_y = points[-1]
            send_mouse_move(last_x, last_y)

        finally:
            if gc_was_enabled:
                gc.enable()
