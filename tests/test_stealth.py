"""
Unit Tests for StealthCore & Anti-Detection Physics
"""

import unittest
from shohoj_macro.core.stealth_core import StealthCore
from shohoj_macro.core.bio_rhythm import BioRhythmEngine


class TestStealth(unittest.TestCase):
    def test_human_click_hold_distribution(self):
        holds = [StealthCore.calculate_human_click_hold_ms() for _ in range(100)]
        for h in holds:
            self.assertGreaterEqual(h, 40.0)
            self.assertLessEqual(h, 150.0)

    def test_human_keypress_hold_distribution(self):
        holds = [StealthCore.calculate_human_keypress_hold_ms() for _ in range(100)]
        for h in holds:
            self.assertGreaterEqual(h, 30.0)
            self.assertLessEqual(h, 120.0)

    def test_bio_rhythm_speed_multiplier(self):
        engine = BioRhythmEngine(fatigue_enabled=True)
        mult = engine.get_speed_multiplier()
        self.assertGreaterEqual(mult, 0.8)
        self.assertLessEqual(mult, 1.25)


if __name__ == "__main__":
    unittest.main()
