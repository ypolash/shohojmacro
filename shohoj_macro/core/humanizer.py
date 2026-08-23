"""
Humanizer Physics & Biomechanical Kinematics Engine (v2.0.0 Enterprise)
Implements Quintic Minimum-Jerk Splines, 8-12Hz Physiological Rest Tremors,
Slow Organic Wandering Curves, and 2D Gaussian Click Area Dispersion.
"""

import math
import random
import time
from typing import Optional, Callable
from shohoj_macro.utils.win32_input import (
    get_cursor_pos,
    send_mouse_move,
    send_mouse_scroll,
)
from shohoj_macro.utils.timer import hires_sleep
from shohoj_macro.core.stealth_core import StealthCore


class HumanizerEngine:
    """Biomechanical human kinematics and organic trajectory generator."""

    @staticmethod
    def sample_gaussian_point_in_circle(center_x: int, center_y: int, radius: int) -> tuple[int, int]:
        """
        Samples a 2D coordinate inside a circle of radius R with 2D Gaussian density (sigma = R/3).
        Clicks cluster naturally near the center without robotic uniformity.
        """
        if radius <= 0:
            return center_x, center_y

        sigma = radius / 3.0
        # Box-Muller transform
        dx = random.gauss(0, sigma)
        dy = random.gauss(0, sigma)
        dist = math.hypot(dx, dy)

        if dist > radius:
            scale = (radius - 0.5) / dist
            dx *= scale
            dy *= scale

        px = int(round(center_x + dx))
        py = int(round(center_y + dy))

        # Ensure strict integer containment <= radius
        while math.hypot(px - center_x, py - center_y) > radius and radius > 0:
            if abs(px - center_x) >= abs(py - center_y):
                px += 1 if px < center_x else -1
            else:
                py += 1 if py < center_y else -1

        return px, py

    @staticmethod
    def generate_smooth_trajectory(
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        num_steps: int = 50,
        tremor_scale: float = 0.35,
    ) -> list[tuple[int, int]]:
        """
        Generates a smooth, natural human trajectory using a Quintic Minimum-Jerk curve
        with gentle organic curvature and 8-12Hz physiological resting tremor.
        """
        if start_x == end_x and start_y == end_y:
            return [(start_x, start_y)]

        dx = end_x - start_x
        dy = end_y - start_y
        dist = math.hypot(dx, dy)

        if dist <= 3.0:
            return [(start_x, start_y), (end_x, end_y)]

        # Perpendicular normal vector for natural hand arc
        perp_x = -dy / dist
        perp_y = dx / dist

        # Gentle curvature offset (max 35px or 18% of distance)
        arc_offset = min(35.0, dist * 0.18) * random.uniform(-0.8, 0.8)

        # Control point for smooth quadratic/cubic curve
        mid_x = (start_x + end_x) / 2.0 + perp_x * arc_offset
        mid_y = (start_y + end_y) / 2.0 + perp_y * arc_offset

        points = []
        steps = max(15, min(num_steps, int(dist / 5.0)))

        # Multi-harmonic frequencies for 8-12Hz physiological tremor
        f1 = random.uniform(8.0, 10.0)
        f2 = random.uniform(10.5, 12.5)

        for i in range(steps + 1):
            t_linear = i / float(steps)
            # Quintic Minimum-Jerk polynomial easing: 10t^3 - 15t^4 + 6t^5
            t = t_linear * t_linear * t_linear * (10.0 - 15.0 * t_linear + 6.0 * t_linear * t_linear)

            # Quadratic Bezier formulation
            omt = 1.0 - t
            bx = omt * omt * start_x + 2.0 * omt * t * mid_x + t * t * end_x
            by = omt * omt * start_y + 2.0 * omt * t * mid_y + t * t * end_y

            # Biological tremor simulation (multi-sine wave scaled by velocity bell curve)
            if 0 < i < steps:
                bell = math.sin(t_linear * math.pi)
                t_sec = t_linear * 0.4
                tremor_x = (math.sin(2 * math.pi * f1 * t_sec) + 0.5 * math.cos(2 * math.pi * f2 * t_sec)) * (tremor_scale * bell)
                tremor_y = (math.cos(2 * math.pi * f1 * t_sec) + 0.5 * math.sin(2 * math.pi * f2 * t_sec)) * (tremor_scale * bell)
            else:
                tremor_x, tremor_y = 0.0, 0.0

            points.append((int(round(bx + tremor_x)), int(round(by + tremor_y))))

        points[-1] = (end_x, end_y)
        return points

    @classmethod
    def generate_windmouse_trajectory(
        cls, start_x: int, start_y: int, dest_x: int, dest_y: int, **kwargs
    ) -> list[tuple[int, int]]:
        dist = math.hypot(dest_x - start_x, dest_y - start_y)
        steps = max(20, min(100, int(dist / 6.0)))
        return cls.generate_smooth_trajectory(start_x, start_y, dest_x, dest_y, num_steps=steps)

    @classmethod
    def generate_bezier_trajectory(
        cls, start_x: int, start_y: int, end_x: int, end_y: int, num_steps: int = 50
    ) -> list[tuple[int, int]]:
        return cls.generate_smooth_trajectory(start_x, start_y, end_x, end_y, num_steps=num_steps)

    @classmethod
    def move_humanized(
        cls,
        dest_x: int,
        dest_y: int,
        duration_ms: float = 240.0,
        curve_type: str = "windmouse",
        cancel_check_fn: Optional[Callable[[], bool]] = None,
    ):
        """Moves cursor from current position to (dest_x, dest_y) in a fluid, natural arc."""
        start_x, start_y = get_cursor_pos()
        if start_x == dest_x and start_y == dest_y:
            return

        dist = math.hypot(dest_x - start_x, dest_y - start_y)
        if dist < 3.0:
            send_mouse_move(dest_x, dest_y)
            return

        if curve_type == "instant":
            send_mouse_move(dest_x, dest_y)
            return
        elif curve_type == "linear":
            steps = max(10, int(dist / 8.0))
            trajectory = [
                (
                    int(round(start_x + (dest_x - start_x) * (i / float(steps)))),
                    int(round(start_y + (dest_y - start_y) * (i / float(steps)))),
                )
                for i in range(steps + 1)
            ]
        else:
            trajectory = cls.generate_smooth_trajectory(start_x, start_y, dest_x, dest_y)

        StealthCore.stream_trajectory_points(
            trajectory,
            total_duration_ms=duration_ms,
            hz_rate=300,
            cancel_check_fn=cancel_check_fn,
        )

    @classmethod
    def perform_slow_organic_wander(
        cls,
        duration_ms: float = 1200.0,
        speed_profile: str = "slow",  # slow, natural, brisk
        zone_bounds: Optional[tuple[int, int, int, int]] = None,  # (x, y, w, h)
        cancel_check_fn: Optional[Callable[[], bool]] = None,
    ):
        """
        Slow organic wandering / reading presence motion.
        Meanders gently across screen or designated area simulating human attention.
        """
        start_x, start_y = get_cursor_pos()
        end_time = time.perf_counter() + (duration_ms / 1000.0)

        # Speed settings in pixels per second
        speed_map = {
            "slow": (120.0, 200.0),
            "natural": (280.0, 450.0),
            "brisk": (550.0, 800.0),
        }
        min_spd, max_spd = speed_map.get(speed_profile, (140.0, 220.0))

        curr_x, curr_y = start_x, start_y

        while time.perf_counter() < end_time:
            if cancel_check_fn and cancel_check_fn():
                break

            # Pick next waypoint within 60-160px of current position
            angle = random.uniform(0, 2 * math.pi)
            step_len = random.uniform(60, 160)
            target_x = int(curr_x + math.cos(angle) * step_len)
            target_y = int(curr_y + math.sin(angle) * step_len)

            # Clamp to zone bounds or screen bounds
            if zone_bounds:
                zx, zy, zw, zh = zone_bounds
                target_x = max(zx, min(zx + zw, target_x))
                target_y = max(zy, min(zy + zh, target_y))

            dist = math.hypot(target_x - curr_x, target_y - curr_y)
            speed = random.uniform(min_spd, max_spd)
            move_dur_ms = max(100.0, (dist / speed) * 1000.0)

            cls.move_humanized(
                target_x,
                target_y,
                duration_ms=move_dur_ms,
                curve_type="windmouse",
                cancel_check_fn=cancel_check_fn,
            )
            curr_x, curr_y = target_x, target_y

            # Idle glance pause
            idle_pause = random.uniform(0.08, 0.25)
            hires_sleep(idle_pause)

    @classmethod
    def perform_human_wander_zone(
        cls,
        center_x: int,
        center_y: int,
        radius: int = 40,
        duration_ms: float = 800.0,
        return_to_origin: bool = True,
        cancel_check_fn: Optional[Callable[[], bool]] = None,
    ):
        """Simulates human hand gently resting/hovering inside a designated circle."""
        start_x, start_y = get_cursor_pos()
        end_time = time.perf_counter() + (duration_ms / 1000.0)

        while time.perf_counter() < end_time:
            if cancel_check_fn and cancel_check_fn():
                break

            target_x, target_y = cls.sample_gaussian_point_in_circle(center_x, center_y, radius)
            move_time = random.uniform(140.0, 260.0)
            cls.move_humanized(target_x, target_y, duration_ms=move_time, curve_type="windmouse", cancel_check_fn=cancel_check_fn)
            idle_pause = random.uniform(0.12, 0.28)
            hires_sleep(idle_pause)

        if return_to_origin and not (cancel_check_fn and cancel_check_fn()):
            cls.move_humanized(start_x, start_y, duration_ms=180.0, curve_type="bezier", cancel_check_fn=cancel_check_fn)

    @classmethod
    def perform_human_scroll_peek(
        cls,
        scroll_notches: int = -4,
        peek_duration_ms: float = 1400.0,
        cancel_check_fn: Optional[Callable[[], bool]] = None,
    ):
        """Non-clashing simulated browsing scroll with exact zero net displacement."""
        if scroll_notches == 0:
            return

        direction = 1 if scroll_notches > 0 else -1
        total_steps = abs(scroll_notches)

        # 1. Smooth human scroll down with easing
        for step in range(total_steps):
            if cancel_check_fn and cancel_check_fn():
                return
            send_mouse_scroll(dy=direction)
            pause = random.uniform(0.05, 0.12)
            hires_sleep(pause)

        # 2. Reading pause
        glance_time = peek_duration_ms / 1000.0
        start_glance = time.perf_counter()
        while time.perf_counter() - start_glance < glance_time:
            if cancel_check_fn and cancel_check_fn():
                return
            hires_sleep(0.05)

        # 3. Exact reverse scroll back
        reverse_direction = -direction
        for step in range(total_steps):
            if cancel_check_fn and cancel_check_fn():
                return
            send_mouse_scroll(dy=reverse_direction)
            pause = random.uniform(0.04, 0.09)
            hires_sleep(pause)
