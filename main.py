"""
Shohoj Macro - Master Entry Point
Developed by Polash Khan (ypolash2)
"""

import sys
import ctypes
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from shohoj_macro.gui.app import ShohojMacroStudio
from shohoj_macro.version import __app_name__, __version__, __author__


def is_admin() -> bool:
    """Checks if running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def main():
    print(f"==================================================")
    print(f"  {__app_name__} v{__version__}")
    print(f"  Developed by {__author__} (ypolash2)")
    print(f"  Admin Mode: {'Elevated (Full Access)' if is_admin() else 'User Mode'}")
    print(f"==================================================")

    app = ShohojMacroStudio()
    app.mainloop()


if __name__ == "__main__":
    main()
