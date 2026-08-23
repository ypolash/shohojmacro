"""
Unit Tests for Zero-AI CV Engine & Template Matching (v2.0.0 Enterprise)
"""

import unittest
import numpy as np
import cv2
from shohoj_macro.core.cv_engine import CVTemplateMatcher, VisualMatchResult


class TestCVEngine(unittest.TestCase):
    def setUp(self):
        # Create a synthetic canvas with distinct high-contrast geometric pattern
        self.canvas = np.zeros((300, 400, 3), dtype=np.uint8)
        # Background gradient
        for y in range(300):
            self.canvas[y, :, :] = (y % 50) + 20

        # Draw distinct patterned target at (80, 50)
        cv2.rectangle(self.canvas, (80, 50), (160, 100), (0, 240, 255), -1)
        cv2.circle(self.canvas, (120, 75), 15, (255, 0, 128), -1)
        cv2.line(self.canvas, (85, 55), (155, 95), (255, 255, 255), 2)

        self.template = self.canvas[50:100, 80:160].copy()

    def test_base64_serialization_roundtrip(self):
        b64 = CVTemplateMatcher.encode_image_to_base64(self.template)
        self.assertIsInstance(b64, str)
        self.assertGreater(len(b64), 20)

        decoded = CVTemplateMatcher.decode_base64_to_image(b64)
        self.assertEqual(decoded.shape, self.template.shape)
        np.testing.assert_array_equal(decoded, self.template)

    def test_template_match_synthetic(self):
        gray_canvas = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(gray_canvas, gray_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        self.assertAlmostEqual(max_val, 1.0, places=3)
        self.assertEqual(max_loc, (80, 50))


if __name__ == "__main__":
    unittest.main()
