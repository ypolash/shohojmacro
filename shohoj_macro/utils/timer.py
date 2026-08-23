"""
High-Resolution Timing & Windows Multimedia Timer Wrapper
Ensures sub-millisecond accuracy without Windows 15.6ms scheduler jitter.
"""

import time
import ctypes
import sys

# Windows Multimedia Timer functions
_winmm = None
_time_period_active = False

if sys.platform == "win32":
    try:
        _winmm = ctypes.WinDLL("winmm.dll")
        # Set Windows timer resolution to 1ms
        if _winmm.timeBeginPeriod(1) == 0:
            _time_period_active = True
    except Exception:
        _winmm = None


def cleanup_timer():
    """Restores default Windows timer resolution."""
    global _time_period_active
    if _time_period_active and _winmm:
        try:
            _winmm.timeEndPeriod(1)
            _time_period_active = False
        except Exception:
            pass


def hires_sleep(seconds: float):
    """
    Sub-millisecond hybrid sleep:
    Uses OS sleep for the bulk of duration (saving CPU),
    and tight perf_counter spin-loop for the last 1.5ms to achieve microsecond accuracy.
    """
    if seconds <= 0:
        return

    start = time.perf_counter()
    target = start + seconds

    # Coarse sleep up to 1.5ms before target
    remaining = target - time.perf_counter()
    if remaining > 0.002:
        time.sleep(remaining - 0.0015)

    # Fine-grained spin-wait
    while time.perf_counter() < target:
        pass


def hires_sleep_ms(milliseconds: float):
    """Sleep for specified milliseconds with sub-ms accuracy."""
    hires_sleep(milliseconds / 1000.0)


class PrecisionTimer:
    """High-resolution stopwatch for measuring execution intervals."""

    def __init__(self):
        self._start_time = time.perf_counter()
        self._last_checkpoint = self._start_time

    def reset(self):
        self._start_time = time.perf_counter()
        self._last_checkpoint = self._start_time

    def elapsed_seconds(self) -> float:
        return time.perf_counter() - self._start_time

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._start_time) * 1000.0

    def delta_ms(self) -> float:
        """Returns elapsed ms since last checkpoint and updates checkpoint."""
        now = time.perf_counter()
        dt = (now - self._last_checkpoint) * 1000.0
        self._last_checkpoint = now
        return dt
