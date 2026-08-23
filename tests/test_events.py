"""
Unit Tests for Shohoj Macro Event AST & Serialization
"""

import unittest
from shohoj_macro.core.events import MacroEvent, EventType, ErrorPolicy


class TestMacroEvents(unittest.TestCase):
    def test_event_creation_and_defaults(self):
        ev = MacroEvent(event_type=EventType.MOUSE_CLICK, x=100, y=200, button="left")
        self.assertEqual(ev.event_type, EventType.MOUSE_CLICK)
        self.assertEqual(ev.x, 100)
        self.assertEqual(ev.y, 200)
        self.assertEqual(ev.button, "left")
        self.assertTrue(ev.enabled)
        self.assertEqual(ev.error_policy, ErrorPolicy.STOP)

    def test_serialization_roundtrip(self):
        ev = MacroEvent(
            event_type=EventType.HUMAN_WANDER_ZONE,
            x=350,
            y=420,
            zone_radius=50,
            duration_ms=1200.0,
            error_policy=ErrorPolicy.SKIP,
            comment="Test Wander Zone",
        )
        d = ev.to_dict()
        self.assertEqual(d["event_type"], "HUMAN_WANDER_ZONE")
        self.assertEqual(d["error_policy"], "SKIP")

        restored = MacroEvent.from_dict(d)
        self.assertEqual(restored.event_type, EventType.HUMAN_WANDER_ZONE)
        self.assertEqual(restored.x, 350)
        self.assertEqual(restored.y, 420)
        self.assertEqual(restored.zone_radius, 50)
        self.assertEqual(restored.error_policy, ErrorPolicy.SKIP)

    def test_event_summaries(self):
        ev_click = MacroEvent(event_type=EventType.MOUSE_CLICK, x=50, y=80, button="right", human_target_radius=15)
        self.assertIn("Right Click", ev_click.get_summary())
        self.assertIn("±15px", ev_click.get_summary())

        ev_type = MacroEvent(event_type=EventType.TEXT_TYPE, text="Hello World", wpm=80)
        self.assertIn("Hello World", ev_type.get_summary())


if __name__ == "__main__":
    unittest.main()
