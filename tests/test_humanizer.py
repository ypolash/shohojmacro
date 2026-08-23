"""
Unit Tests for Humanizer Physics: WindMouse, Bézier & Gaussian Dispersion
"""

import unittest
import math
from shohoj_macro.core.humanizer import HumanizerEngine


class TestHumanizer(unittest.TestCase):
    def test_gaussian_point_in_circle_bounds(self):
        cx, cy, radius = 500, 500, 30
        for _ in range(100):
            gx, gy = HumanizerEngine.sample_gaussian_point_in_circle(cx, cy, radius)
            dist = math.hypot(gx - cx, gy - cy)
            self.assertLessEqual(dist, radius + 0.001)

    def test_bezier_trajectory_endpoints(self):
        start_x, start_y = 100, 100
        end_x, end_y = 800, 600
        points = HumanizerEngine.generate_bezier_trajectory(start_x, start_y, end_x, end_y, num_steps=50)

        self.assertGreater(len(points), 20)
        self.assertEqual(points[0], (start_x, start_y))
        self.assertEqual(points[-1], (end_x, end_y))

    def test_windmouse_trajectory_generation(self):
        start_x, start_y = 200, 200
        dest_x, dest_y = 600, 700
        points = HumanizerEngine.generate_windmouse_trajectory(start_x, start_y, dest_x, dest_y)

        self.assertGreater(len(points), 5)
        self.assertEqual(points[0], (start_x, start_y))
        self.assertEqual(points[-1], (dest_x, dest_y))


if __name__ == "__main__":
    unittest.main()
