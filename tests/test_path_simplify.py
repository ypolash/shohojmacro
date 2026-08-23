"""
Unit Tests for Ramer-Douglas-Peucker (RDP) Path Simplification
"""

import unittest
from shohoj_macro.utils.path_simplify import rdp_simplify


class TestPathSimplify(unittest.TestCase):
    def test_straight_line_compression(self):
        # 10 collinear points on a straight line
        straight = [(float(i * 10), float(i * 10)) for i in range(10)]
        simplified = rdp_simplify(straight, epsilon=1.0)
        # Should reduce to only start and end points
        self.assertEqual(len(simplified), 2)
        self.assertEqual(simplified[0], straight[0])
        self.assertEqual(simplified[-1], straight[-1])

    def test_corner_retention(self):
        # Path with sharp corner
        path = [(0.0, 0.0), (50.0, 0.0), (100.0, 0.0), (100.0, 50.0), (100.0, 100.0)]
        simplified = rdp_simplify(path, epsilon=2.0)
        self.assertIn((100.0, 0.0), simplified)
        self.assertEqual(len(simplified), 3)


if __name__ == "__main__":
    unittest.main()
