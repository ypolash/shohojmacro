"""
Unit Tests for Dynamic CSV Engine & Variable Interpolation
"""

import unittest
import tempfile
import os
from shohoj_macro.core.csv_engine import CSVDataEngine


class TestCSVEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CSVDataEngine()

        # Create temporary CSV file
        self.temp_file = tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8")
        self.temp_file.write("username,email,password\n")
        self.temp_file.write("polash,polash@example.com,secret123\n")
        self.temp_file.write("john_doe,john@domain.org,pass456\n")
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_load_csv(self):
        success, msg = self.engine.load_file(self.temp_file.name)
        self.assertTrue(success)
        self.assertEqual(self.engine.get_row_count(), 2)
        self.assertEqual(self.engine.headers, ["username", "email", "password"])

    def test_variable_interpolation(self):
        self.engine.load_file(self.temp_file.name)

        text_template = "User: {{username}} | Email: {{email}}"
        row_0 = self.engine.interpolate_text(text_template, 0)
        self.assertEqual(row_0, "User: polash | Email: polash@example.com")

        row_1 = self.engine.interpolate_text(text_template, 1)
        self.assertEqual(row_1, "User: john_doe | Email: john@domain.org")

    def test_missing_variable_validation(self):
        self.engine.load_file(self.temp_file.name)
        unmapped = self.engine.validate_variables("{{username}} {{non_existent}}")
        self.assertEqual(unmapped, ["non_existent"])

    def test_mark_row_status_persists_to_disk(self):
        self.engine.load_file(self.temp_file.name)
        
        callback_log = []
        self.engine.on_status_change = lambda idx, status: callback_log.append((idx, status))
        
        # Mark row 0 as "Polash"
        self.engine.mark_row_status(0, "Status", "Polash")
        
        # Verify in memory
        row_0 = self.engine.get_row_data(0)
        self.assertEqual(row_0.get("Status"), "Polash")
        self.assertEqual(callback_log, [(0, "Polash")])
        
        # Verify persisted to disk by loading in fresh engine
        fresh_engine = CSVDataEngine()
        success, _ = fresh_engine.load_file(self.temp_file.name)
        self.assertTrue(success)
        self.assertIn("Status", fresh_engine.headers)
        fresh_row_0 = fresh_engine.get_row_data(0)
        self.assertEqual(fresh_row_0.get("Status"), "Polash")


if __name__ == "__main__":
    unittest.main()
