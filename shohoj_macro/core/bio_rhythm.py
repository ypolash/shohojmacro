"""
Bio-Rhythm & Session Fatigue Engine
Simulates natural human fatigue and pacing variations over marathon macro sessions.
"""

import random
import time
import math


class BioRhythmEngine:
    """Calculates organic session drift and micro-hesitation variance."""

    def __init__(self, fatigue_enabled: bool = True):
        self.enabled = fatigue_enabled
        self.session_start_time = time.perf_counter()
        self.loop_counter = 0

    def reset_session(self):
        self.session_start_time = time.perf_counter()
        self.loop_counter = 0

    def on_loop_completed(self):
        self.loop_counter += 1

    def get_speed_multiplier(self) -> float:
        """
        Returns a time-varying speed multiplier (e.g. 0.92 to 1.08)
        following a smooth sinusoidal bio-rhythm curve.
        """
        if not self.enabled:
            return 1.0

        elapsed_mins = (time.perf_counter() - self.session_start_time) / 60.0
        # Multi-frequency wave simulating focus cycles
        wave1 = math.sin(elapsed_mins * 0.4) * 0.05
        wave2 = math.cos(elapsed_mins * 0.15) * 0.04
        jitter = random.uniform(-0.02, 0.02)
        return max(0.85, min(1.18, 1.0 + wave1 + wave2 + jitter))

    def should_inject_micro_hesitation(self) -> bool:
        """Rare 3% chance of natural 150-400ms human pause."""
        if not self.enabled:
            return False
        return random.random() < 0.03

    def get_micro_hesitation_duration_sec(self) -> float:
        return random.uniform(0.15, 0.42)
