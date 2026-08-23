"""
Unit Tests for Win32 Input Helpers and Scan Code Mappings
"""

import unittest
from shohoj_macro.utils.win32_input import map_vk_to_scancode, char_to_vk_and_scan


class TestWin32Input(unittest.TestCase):
    def test_scan_code_mappings(self):
        # VK_RETURN = 0x0D -> Scan Code = 0x1C (28)
        scan = map_vk_to_scancode(0x0D)
        self.assertEqual(scan, 28)

        # VK_SPACE = 0x20 -> Scan Code = 0x39 (57)
        scan_space = map_vk_to_scancode(0x20)
        self.assertEqual(scan_space, 57)

    def test_char_to_vk_and_scan(self):
        vk, scan, shift = char_to_vk_and_scan("A")
        self.assertGreater(vk, 0)
        self.assertGreater(scan, 0)
        self.assertTrue(shift)

        vk_lower, scan_lower, shift_lower = char_to_vk_and_scan("a")
        self.assertGreater(vk_lower, 0)
        self.assertGreater(scan_lower, 0)
        self.assertFalse(shift_lower)


if __name__ == "__main__":
    unittest.main()
