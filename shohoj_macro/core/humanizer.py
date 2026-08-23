"""
Humanizer Physics Engine: Minimum-Jerk Splines, Smooth Bézier Curves & Gaussian Area Dispersion
Generates fluid, lifelike human mouse kinematics without erratic or violent cursor shaking.
"""

import math
import random
import time
from shohoj_macro.utils.win32_input import (
    get_cursor_pos,
    send_mouse_move,
    send_mouse_scroll,
)
from shohoj_macro.utils.timer import hires_sleep
from shohoj_macro.core.stealth_core import StealthCore


class HumanizerEngine:
    """Physics-based human kinematics and organic trajectory generator."""

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

        # Ensure integer rounding stays strictly within radius
        int_dist = math.hypot(px - center_x, py - center_y)
        if int_dist > radius and radius > 0:
            scale = (radius - 0.5) / int_dist
            px = int(round(center_x + (px - center_x) * scale))
            py = int(round(center_y + (py - center_y) * scale))

        return px, py

    @staticmethod
    def generate_smooth_trajectory(
        start_x: int, start_y: int, end_x: int, end_y: int, num_steps: int = 50
    ) -> list[tuple[int, int]]:
        """
        Generates a smooth, natural human trajectory using a Quintic Minimum-Jerk curve
        with gentle organic curvature and realistic deceleration.
        Zero chaotic shaking or high-frequency oscillation.
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
        # Dynamic step count based on distance
        steps = max(15, min(num_steps, int(dist / 5.0)))

        for i in range(steps + 1):
            t_linear = i / float(steps)
            # Quintic Minimum-Jerk polynomial easing: 10t^3 - 15t^4 + 6t^5
            # Produces zero acceleration at endpoints and peak smooth velocity in middle
            t = t_linear * t_linear * t_linear * (10.0 - 15.0 * t_linear + 6.0 * t_linear * t_linear)

            # Quadratic Bezier formulation
            omt = 1.0 - t
            bx = omt * omt * start_x + 2.0 * omt * t * mid_x + t * t * end_x
            by = omt * omt * start_y + 2.0 * omt * t * mid_y + t * t * end_y

            # Micro-tremor (gentle low-pass noise: max 0.35px)
            if 0 < i < steps:
                jitter_factor = math.sin(t_linear * math.pi) * 0.35
                jitter_x = random.uniform(-jitter_factor, jitter_factor)
                jitter_y = random.uniform(-jitter_factor, jitter_factor)
            else:
                jitter_x, jitter_y = 0.0, 0.0

            points.append((int(round(bx + jitter_x)), int(round(by + jitter_y))))

        points[-1] = (end_x, end_y)
        return points

    @classmethod
    def generate_windmouse_trajectory(
        cls, start_x: int, start_y: int, dest_x: int, dest_y: int, **kwargs
    ) -> list[tuple[int, int]]:
        """
        WindMouse trajectory wrapper utilizing stable smooth curvature.
        Guarantees smooth glide without chaotic oscillations.
        """
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
        cancel_check_fn=None,
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
    def perform_human_wander_zone(
        cls,
        center_x: int,
        center_y: int,
        radius: int = 40,
        duration_ms: float = 800.0,
        return_to_origin: bool = True,
        cancel_check_fn=None,
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
        cancel_check_fn=None,
    ):
        """
        Non-clashing simulated browsing scroll with exact zero net displacement.
        """
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
