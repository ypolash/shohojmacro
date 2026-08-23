"""
Unit Tests for Macro File Storage (.shj) & Exporters
"""

import unittest
import os
import tempfile
from shohoj_macro.core.events import MacroEvent, EventType
from shohoj_macro.core.storage import MacroStorage
from shohoj_macro.core.exporter import MacroExporter


class TestStorageAndExporter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.events = [
            MacroEvent(event_type=EventType.MOUSE_CLICK, x=250, y=350, button="left", human_target_radius=10),
            MacroEvent(event_type=EventType.TEXT_TYPE, text="Automated with Shohoj Macro", wpm=90),
            MacroEvent(event_type=EventType.DELAY, delay_ms=500.0),
        ]

    def test_save_and_load_shj(self):
        filepath = os.path.join(self.test_dir, "test_sample.shj")
        saved = MacroStorage.save_macro_to_file(filepath, self.events, name="Sample Test")
        self.assertTrue(saved)
        self.assertTrue(os.path.exists(filepath))

        loaded_events, meta = MacroStorage.load_macro_from_file(filepath)
        self.assertEqual(len(loaded_events), 3)
        self.assertEqual(meta.get("name"), "Sample Test")
        self.assertEqual(loaded_events[0].x, 250)
        self.assertEqual(loaded_events[1].text, "Automated with Shohoj Macro")

    def test_python_export(self):
        filepath = os.path.join(self.test_dir, "exported_macro.py")
        exported = MacroExporter.export_to_python_script(self.events, filepath, loops=2, speed=1.5)
        self.assertTrue(exported)
        self.assertTrue(os.path.exists(filepath))

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Shohoj Macro", content)
        self.assertIn("Automated with Shohoj Macro", content)

    def test_ahk_export(self):
        filepath = os.path.join(self.test_dir, "exported_macro.ahk")
        exported = MacroExporter.export_to_ahk_script(self.events, filepath, loops=1, speed=1.0)
        self.assertTrue(exported)
        self.assertTrue(os.path.exists(filepath))

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("MouseClick", content)


if __name__ == "__main__":
    unittest.main()
