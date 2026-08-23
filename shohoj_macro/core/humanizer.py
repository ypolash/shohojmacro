"""
Humanizer Physics Engine: WindMouse, Bézier Splines, Gaussian Click Scatter & Scroll-Peek
Generates lifelike human mouse kinematics indistinguishable from manual usage.
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
    """Physics-based trajectory and auxiliary behavior generator."""

    @staticmethod
    def sample_gaussian_point_in_circle(center_x: int, center_y: int, radius: int) -> tuple[int, int]:
        """
        Samples a 2D coordinate inside a circle of radius R with 2D Gaussian density (sigma = R/3).
        Clicks naturally cluster near the center just like real human finger taps.
        """
        if radius <= 0:
            return center_x, center_y

        sigma = radius / 3.0
        # Box-Muller transform for 2D Gaussian
        dx = random.gauss(0, sigma)
        dy = random.gauss(0, sigma)
        dist = math.hypot(dx, dy)

        if dist > radius:
            # Clamp to boundary if beyond radius
            scale = radius / dist
            dx *= scale
            dy *= scale

        return int(round(center_x + dx)), int(round(center_y + dy))

    @staticmethod
    def generate_bezier_trajectory(
        start_x: int, start_y: int, end_x: int, end_y: int, num_steps: int = 60
    ) -> list[tuple[int, int]]:
        """
        Generates a Cubic Bézier curve with randomized control points and Fitts's law velocity easing.
        """
        if start_x == end_x and start_y == end_y:
            return [(start_x, start_y)]

        dx = end_x - start_x
        dy = end_y - start_y
        dist = math.hypot(dx, dy)

        # Generate control points offset perpendicular to trajectory
        perp_x = -dy / (dist + 0.001)
        perp_y = dx / (dist + 0.001)

        offset_scale = min(120.0, dist * 0.35)
        offset1 = random.uniform(-offset_scale, offset_scale)
        offset2 = random.uniform(-offset_scale, offset_scale)

        p0 = (float(start_x), float(start_y))
        p1 = (
            start_x + dx * 0.33 + perp_x * offset1,
            start_y + dy * 0.33 + perp_y * offset1,
        )
        p2 = (
            start_x + dx * 0.66 + perp_x * offset2,
            start_y + dy * 0.66 + perp_y * offset2,
        )
        p3 = (float(end_x), float(end_y))

        points = []
        for i in range(num_steps + 1):
            # Fitts's Law easing (slow start, fast middle, slow end)
            t_linear = i / float(num_steps)
            # Smoothstep curve: 3t^2 - 2t^3
            t = t_linear * t_linear * (3.0 - 2.0 * t_linear)

            # Cubic Bezier formula
            omt = 1.0 - t
            bx = omt**3 * p0[0] + 3 * omt**2 * t * p1[0] + 3 * omt * t**2 * p2[0] + t**3 * p3[0]
            by = omt**3 * p0[1] + 3 * omt**2 * t * p1[1] + 3 * omt * t**2 * p2[1] + t**3 * p3[1]

            # Add subtle sub-pixel micro-tremor
            jitter_x = random.uniform(-0.6, 0.6)
            jitter_y = random.uniform(-0.6, 0.6)

            points.append((int(round(bx + jitter_x)), int(round(by + jitter_y))))

        points[-1] = (end_x, end_y)
        return points

    @staticmethod
    def generate_windmouse_trajectory(
        start_x: int,
        start_y: int,
        dest_x: int,
        dest_y: int,
        gravity: float = 9.0,
        wind: float = 3.0,
        min_wait: float = 2.0,
        max_wait: float = 4.0,
        max_step: float = 12.0,
        target_area: float = 3.0,
    ) -> list[tuple[int, int]]:
        """
        WindMouse algorithm: models natural human hand physics (gravity pull, wind resistance,
        mass inertia, and random muscle tremors).
        """
        current_x = float(start_x)
        current_y = float(start_y)
        v_x = 0.0
        v_y = 0.0
        w_x = 0.0
        w_y = 0.0

        points = [(start_x, start_y)]
        dist = math.hypot(dest_x - start_x, dest_y - start_y)

        while dist > 1.0:
            wind = min(wind, dist)
            if dist >= target_area:
                w_x = w_x / math.sqrt(3) + (random.random() * (wind * 2 + 1) - wind) / math.sqrt(5)
                w_y = w_y / math.sqrt(3) + (random.random() * (wind * 2 + 1) - wind) / math.sqrt(5)
            else:
                w_x /= math.sqrt(3)
                w_y /= math.sqrt(3)
                if max_step < 3:
                    max_step = random.random() * 3 + 3.0
                else:
                    max_step /= math.sqrt(5)

            v_x += w_x + gravity * (dest_x - current_x) / dist
            v_y += w_y + gravity * (dest_y - current_y) / dist

            vel_mag = math.hypot(v_x, v_y)
            if vel_mag > max_step:
                random_dist = max_step / 2.0 + random.random() * (max_step / 2.0)
                v_x = (v_x / vel_mag) * random_dist
                v_y = (v_y / vel_mag) * random_dist

            current_x += v_x
            current_y += v_y
            points.append((int(round(current_x)), int(round(current_y))))

            dist = math.hypot(dest_x - current_x, dest_y - current_y)
            if len(points) > 1000:  # Safety cap
                break

        points.append((dest_x, dest_y))
        return points

    @classmethod
    def move_humanized(
        cls,
        dest_x: int,
        dest_y: int,
        duration_ms: float = 280.0,
        curve_type: str = "windmouse",
        cancel_check_fn=None,
    ):
        """Moves cursor from current position to (dest_x, dest_y) with chosen human curve."""
        start_x, start_y = get_cursor_pos()
        if start_x == dest_x and start_y == dest_y:
            return

        dist = math.hypot(dest_x - start_x, dest_y - start_y)
        # Adapt step count to distance
        steps = max(20, min(140, int(dist / 6.0)))

        if curve_type == "bezier":
            trajectory = cls.generate_bezier_trajectory(start_x, start_y, dest_x, dest_y, steps)
        elif curve_type == "linear":
            trajectory = [
                (
                    int(round(start_x + (dest_x - start_x) * (i / float(steps)))),
                    int(round(start_y + (dest_y - start_y) * (i / float(steps)))),
                )
                for i in range(steps + 1)
            ]
        elif curve_type == "instant":
            send_mouse_move(dest_x, dest_y)
            return
        else:  # Default WindMouse
            trajectory = cls.generate_windmouse_trajectory(start_x, start_y, dest_x, dest_y)

        StealthCore.stream_trajectory_points(
            trajectory,
            total_duration_ms=duration_ms,
            hz_rate=350,
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
        """Simulates human hand resting/wobbling inside a designated circle."""
        start_x, start_y = get_cursor_pos()
        end_time = time.perf_counter() + (duration_ms / 1000.0)

        while time.perf_counter() < end_time:
            if cancel_check_fn and cancel_check_fn():
                break

            target_x, target_y = cls.sample_gaussian_point_in_circle(center_x, center_y, radius)
            move_time = random.uniform(120.0, 240.0)
            cls.move_humanized(target_x, target_y, duration_ms=move_time, curve_type="windmouse", cancel_check_fn=cancel_check_fn)
            idle_pause = random.uniform(0.08, 0.22)
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
        Non-clashing simulated browsing scroll:
        Smoothly scrolls down, pauses for reading, and scrolls back the exact opposite delta (-scroll_notches).
        Guarantees zero net displacement for subsequent macro clicks.
        """
        if scroll_notches == 0:
            return

        direction = 1 if scroll_notches > 0 else -1
        total_steps = abs(scroll_notches)

        # Step 1: Smooth human scroll down with easing
        for step in range(total_steps):
            if cancel_check_fn and cancel_check_fn():
                return
            send_mouse_scroll(dy=direction)
            pause = random.uniform(0.04, 0.12)
            hires_sleep(pause)

        # Step 2: Reading pause
        glance_time = peek_duration_ms / 1000.0
        start_glance = time.perf_counter()
        while time.perf_counter() - start_glance < glance_time:
            if cancel_check_fn and cancel_check_fn():
                return
            hires_sleep(0.05)

        # Step 3: Exact reverse scroll back (Net Zero Displacement)
        reverse_direction = -direction
        for step in range(total_steps):
            if cancel_check_fn and cancel_check_fn():
                return
            send_mouse_scroll(dy=reverse_direction)
            pause = random.uniform(0.03, 0.09)
            hires_sleep(pause)
