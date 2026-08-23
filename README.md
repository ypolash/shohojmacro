# ⚡ Shohoj Macro (সহজ ম্যাক্রো)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-00F0FF?style=for-the-badge)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://microsoft.com)
[![Developer: Polash Khan](https://img.shields.io/badge/Developer-Polash%20Khan%20(ypolash2)-30D158?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ypolash2)

**Shohoj Macro** ("সহজ ম্যাক্রো" - Simple, Intelligent, Indistinguishable Desktop Automation) is a state-of-the-art Windows automation suite developed by **Polash Khan (ypolash2)**.

It combines **sub-millisecond hardware-level input simulation**, **Fitts's Law WindMouse physics**, **human bio-rhythm fatigue modeling**, **zone sniper screen loupe**, and a **companion Manifest V3 browser extension** for 100% `isTrusted` web automation bypassing Cloudflare, DataDome, and anti-bot systems.

---

## 🌟 Key Features

### 🍏 1. Apple-Style Glassmorphism UI & Dynamic Island
- **Liquid Obsidian Theme:** Frosted acrylic glass cards with 1px luminous borders (`#2E344D`), refined typography, and vibrant Apple neon accents.
- **Dynamic Island Mini-HUD:** A floating, pill-shaped glass capsule widget that stays on top of full-screen games and apps showing live pulse status (`● REC 00:14`, `▶ LOOP 3/10`, `Speed: 1.5x`, `[F10: Stop]`).

### 🧠 2. StealthCore & Humanizer Physics Engine
- **WindMouse & Bézier Trajectories:** Natural mouse curves with mass inertia, gravity pull towards target, wind turbulence, and micro-hand tremors.
- **Fitts's Law Velocity Profiles:** Fast acceleration in open space, smooth deceleration near targets with 1–3 px natural micro-overshoots.
- **Gaussian Click Heatmap:** Clicks naturally scatter around target centers in a normal bell curve ($\sigma = R/3$) rather than robotic identical coordinates.
- **Human Hold Times:** Realistic muscle hold durations (Gaussian $70\text{ms} \pm 20\text{ms}$).
- **Non-Clashing Scroll-Peek:** Simulates natural reading/browsing scroll with **exact $-\Delta Y$ zero net displacement** so subsequent macro clicks are 100% synchronized.
- **Bio-Rhythm Fatigue:** Subtly modulates loop speeds ($\pm 5\% - 10\%$) and introduces natural micro-hesitations during long marathon runs.

### 🌐 3. Shohoj Browser Companion (100% Undetectable Web Automation)
- **Zero-CDP & No `navigator.webdriver`:** Avoids browser fingerprint detection traps.
- **Stealth DOM Inspector:** Inspect any web element (button, input, captcha slider) in Chrome/Edge/Firefox. The extension converts its bounding client rect into **Global OS Screen Coordinates**.
- **Physical OS Hardware Execution:** Shohoj Macro moves the physical OS cursor and clicks with Windows `SendInput`, firing authentic DOM events with **`event.isTrusted = true`**!

### 🎯 4. "Zone Sniper" Screen Overlay Tool
- **8x Magnifying Loupe:** Real-time pixel inspector with crosshairs and exact Hex/RGB color sampler.
- **Visual Circle & Radius Drawer:** Click and drag directly over any screen element to define a tolerance circle ($R\text{ px}$) with animated Gaussian scatter dots.

### ⚡ 5. Studio Timeline Editor & Exporters
- Step-by-step visual timeline table with color-coded chips, reordering, duplicate, delete, and inline enable/disable.
- Export macros to **Standalone Python Scripts** (embedding WindMouse physics) or **AutoHotkey (`.ahk`) Scripts**.

---

## ⌨️ Global Hotkeys

| Hotkey | Action | Description |
|---|---|---|
| <kbd>F8</kbd> | **Record / Stop** | Start or stop recording global mouse and keyboard actions |
| <kbd>F9</kbd> | **Play / Pause** | Start, pause, or resume macro playback |
| <kbd>F10</kbd> | **Emergency Stop** | Instant fail-safe abort / kill switch |

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.12, 3.14 on Windows 10/11)
- Install required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Launching Shohoj Macro
```bash
python main.py
```

### 3. Installing the Browser Companion (Chrome / Edge / Brave)
1. Open Chrome or Edge and navigate to `chrome://extensions`.
2. Enable **Developer mode** (top-right toggle).
3. Click **Load unpacked** and select the `d:/macro/browser_extension` folder.
4. Click the Shohoj Macro icon in your browser toolbar to connect!

### 4. Running Automated Tests
```bash
python run_tests.py
```

---

## 🏗️ Project Architecture

```
d:/macro/
├── main.py                                  # Application Entry Point
├── run_tests.py                             # Automated Test Runner (14 Unit Tests)
├── requirements.txt                         # Python Dependencies
├── README.md                                # Documentation
│
├── browser_extension/                       # Manifest V3 Stealth Browser Companion
│   ├── manifest.json                        # MV3 Configuration
│   ├── background.js                        # Keep-alive Service Worker & WebSocket Bridge
│   ├── content.js                           # Stealth DOM Inspector & Coordinate Resolver
│   ├── popup.html / popup.css / popup.js    # Glass Extension Popup UI
│
├── tests/                                   # Automated Test Suite
│   ├── test_events.py                       # AST serialization tests
│   ├── test_humanizer.py                    # WindMouse, Bezier & Gaussian tests
│   ├── test_stealth.py                      # StealthCore & hold time tests
│   ├── test_path_simplify.py                # RDP path compression tests
│   └── test_storage.py                      # Storage & exporter tests
│
└── shohoj_macro/
    ├── version.py                           # Version & Author Metadata (Polash Khan)
    │
    ├── core/                                # Core Engine
    │   ├── events.py                        # Event AST, Block Loops & Conditions
    │   ├── recorder.py                      # Hook Capture + RDP Path Compression
    │   ├── player.py                        # Sub-ms Playback + Error Policies + Focus Lock
    │   ├── stealth_core.py                  # Zero-GC Streaming & Hold Modeling
    │   ├── humanizer.py                     # WindMouse, Bezier, Gaussian Jitter & Scroll-Peek
    │   ├── bio_rhythm.py                    # Fatigue Drift & Session Variance
    │   ├── browser_bridge.py                # Zero-dependency WebSocket Server (Port 8765)
    │   ├── window_tracker.py                # Relative Window Coordinates & Focus Anchor
    │   ├── triggers.py                      # Pixel Color & Visual Condition Matcher
    │   ├── exporter.py                      # Standalone Python & AHK Script Generator
    │   ├── hotkeys.py                       # Global Low-Level Hotkey Dispatcher
    │   ├── storage.py                       # Native .shj File Manager & Library Indexer
    │   └── undo_manager.py                  # Command Pattern Undo/Redo Stack
    │
    ├── gui/                                 # Apple-Style Glassmorphism UI
    │   ├── app.py                           # Main Studio Window
    │   ├── glass_theme.py                   # Theme Tokens, Glass Cards & Buttons
    │   ├── dynamic_island.py                # Floating HUD Capsule Widget
    │   ├── timeline_table.py                # Interactive Timeline & Action Table
    │   ├── trajectory_canvas.py             # Mini Bezier & Mouse Path Previewer
    │   ├── screen_overlay.py                # Zone Sniper Loupe & Visual Circle Drawer
    │   ├── playback_log.py                  # Ring-Buffered Activity Log
    │   ├── macro_library.py                 # Sidebar Saved Macros & Tag Search
    │   ├── browser_panel.py                 # Extension Bridge Status & Web Inspector
    │   ├── action_dialogs.py                # Action Property Editors (Mouse/Key/Delay)
    │   ├── settings_dialog.py               # Preferences, Hotkeys & Error Policies
    │   ├── export_dialog.py                 # Export Format Picker & Feature Matrix
    │   └── about_dialog.py                  # Developer Attribution (Polash Khan)
    │
    └── utils/                               # System Helpers
        ├── timer.py                         # Windows winmm 1ms Multimedia Timer
        ├── win32_input.py                   # Direct ctypes SendInput Hardware Driver
        ├── dpi_helper.py                    # Per-Monitor DPI V2 Geometry
        ├── color_utils.py                   # GDI GetPixel Sampler & RGB Matcher
        └── path_simplify.py                 # Ramer-Douglas-Peucker (RDP) Algorithm
```

---

## 👨‍💻 Developer & Author

* **Lead Architect & Developer:** **Polash Khan**
* **GitHub Profile:** [@ypolash2](https://github.com/ypolash2)
* **Project Name:** **Shohoj Macro** (সহজ ম্যাক্রো)
* **License:** [MIT License](LICENSE)
