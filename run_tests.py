"""
Automated Test Suite Runner for Shohoj Macro
"""

import unittest
import sys
import os

# Ensure root directory is on PATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def run_all_tests():
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\nAll automated tests passed successfully!")
        return 0
    else:
        print(f"\nTests failed! Errors: {len(result.errors)}, Failures: {len(result.failures)}")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
