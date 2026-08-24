# ⚡ Shohoj Macro ("সহজ ম্যাক্রো")
### *Autonomous Stealth Automation, Zero-AI Visual Synchronization & Data Engine for Windows*

[![Release](https://img.shields.io/badge/Release-v2.0.0--Enterprise-00F0FF?style=for-the-badge&logo=windows)](https://github.com/ypolash/shohojmacro)
[![License](https://img.shields.io/badge/License-MIT-30D158?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B%20|%203.14-0A84FF?style=for-the-badge&logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-BF5AF2?style=for-the-badge&logo=windows11)](https://microsoft.com)
[![Stealth](https://img.shields.io/badge/Stealth-Indistinguishable%20Hardware%20Kinematics-FF9F0A?style=for-the-badge)](docs/ARCHITECTURE.md)

**Developed by:** [Polash Khan](https://github.com/ypolash) (`ypolash` / `ypolash2`)  
**Repository:** [https://github.com/ypolash/shohojmacro](https://github.com/ypolash/shohojmacro)

---

## 🌟 What is Shohoj Macro?

**Shohoj Macro** (Bengali: **সহজ ম্যাক্রো** — *"Effortless Macro"*) is a next-generation desktop automation suite for Windows. 

Traditional macro software (AutoHotkey, macro recorders) and web frameworks (Selenium, Puppeteer) are easily detected by modern anti-bot systems (Cloudflare Turnstile, DataDome, Akamai, Vanguard, EasyAntiCheat) because they emit linear robotic cursor movements and fake synthetic events (`event.isTrusted = false`).

**Shohoj Macro completely solves this problem.** It executes actions via **Win32 kernel-level `SendInput` Hardware ScanCodes** and models real human biology using **Quintic Minimum-Jerk Splines**, **8–12Hz physiological resting hand tremors**, and **Gaussian click area dispersion**.

It features an **Apple-style Liquid Obsidian Glassmorphism Studio**, an interactive **Zero-AI Visual Screen Snipper**, a dynamic **CSV Data-Driven Form Engine**, and a companion **Manifest V3 Browser Plugin**.

---

## 🚀 Key Features

```
                                  SHOHOJ MACRO v2.0.0
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │  🍎 Liquid Glassmorphic Studio UI     │  📸 Zero-AI Visual Frame Synchronization │
  │  🏝️ Hardware Anti-Aliased Dynamic HUD │  📊 CSV Dynamic Data Form Injection      │
  │  ⌨️ 100% Hardware Scan-Code Precision  │  🌿 8-12Hz Physiological Hand Tremors    │
  │  🌐 Undetectable Chrome/Edge Companion│  📦 1-Click Portable Executable (.exe)   │
  └─────────────────────────────────────────────────────────────────────────────────┘
```

### 1. 📸 Zero-AI Visual Frame Synchronization & Auto-Adjusting Anchors
- **Freeze-Frame Screen Snipper:** Click `[📸 Snip Anchor]` to freeze the screen with crosshairs and crop any button, badge, or UI element.
- **Dynamic Auto-Adjusting Clicks:** Uses high-speed OpenCV template matching ($< 2\text{ms}$) to locate where the button currently is on screen and **auto-adjusts the mouse click directly on it even if the window moved, resized, or scrolled!**
- **Visual State Guards:** Actions to `Wait Until Frame Appears` or `Wait Until Loading Spinner Vanishes` before proceeding.
- **100% Single-File Portability:** All template snippets are compressed and embedded as Base64 strings directly inside `.shj` macro files.

### 2. 📊 Dynamic CSV Data-Driven Input Engine (Form & Registration Automation)
- **CSV Data Dock:** Load any CSV/Excel dataset (`users.csv`) with automatic encoding detection (`utf-8-sig`, `latin-1`).
- **Dynamic Variable Templating:** Write `"Hello {{first_name}}"` ➔ Tab ➔ `"{{email}}"` ➔ Tab ➔ `"{{password}}"`. Click any variable badge to copy it.
- **Batch Multi-Row Iteration:** Fills and submits **Row 1**, then automatically loops through **Row 2**, **Row 3**, ..., through all $N$ rows!

### 3. 🍎 True Apple Glassmorphism UI & Flawless Dynamic Island
- **Windows 11 DWM Hardware Anti-Aliasing:** Replaces 1-bit transparency keys with native `DwmSetWindowAttribute` + double-buffered rendering for a silky-smooth 60fps pill HUD floating at the top of your screen with **0 black border artifacts**.
- **Live Visual Proof:** Pulsing red record dot (`● REC [00:04] • 14 actions`) and glowing green playback progress badge across all games and full-screen windows.

### 4. ⌨️ 100% Hardware Scan-Code Keystroke Precision
- **Dual-Layer Keyboard Mapping:** Full `VkKeyScanW` + `MapVirtualKeyW` hardware scan-code resolution with guaranteed $35\text{ms} - 55\text{ms}$ human hold times.
- **React / Vue SPA-Safe Form Input:** Includes auto-focus and clear (`Ctrl+A` ➔ `Backspace`) before typing, ensuring modern single-page apps never drop characters.

### 5. 🌿 Biomechanical Kinematics & Slow Organic Wandering
- **Minimum-Jerk Splines ($10t^3 - 15t^4 + 6t^5$):** Smooth Fitts's Law acceleration and deceleration curves without robotic jerkiness.
- **Physiological Rest Tremors:** Injects genuine 8–12Hz harmonic micro-tremors ($\pm 0.2\text{px} - 0.4\text{px}$) that pass deep anti-cheat heuristic inspections.
- **`HUMAN_WANDER_SLOW`:** Gentle reading presence and natural hand resting for anti-AFK stealth.

### 6. 🌐 Undetectable Chrome & Edge Companion Plugin
- Communicates out-of-band over a local RFC6455 WebSocket (`ws://127.0.0.1:8765`).
- 1-click web element picking: captures screen coordinates and triggers true physical OS clicks with **`event.isTrusted === true`**, effortlessly bypassing Cloudflare Turnstile and DataDome.

---

## ⚡ Quick Start

### Option 1: Standalone Windows Executable (`.exe`)
No Python installation required!
1. Download or clone this repository.
2. Run [`dist/ShohojMacro/ShohojMacro.exe`](dist/ShohojMacro/ShohojMacro.exe) or double-click [`Launch_Shohoj_Macro.bat`](Launch_Shohoj_Macro.bat).
3. For zero-console background stealth mode, double-click [`Launch_Silent.vbs`](Launch_Silent.vbs).

### Option 2: Running from Source (Python 3.11–3.14)
```bash
# Clone the repository
git clone https://github.com/ypolash/shohojmacro.git
cd shohojmacro

# Install dependencies
pip install -r requirements.txt

# Launch Shohoj Macro Studio
python main.py
```

### Option 3: Rebuilding the Executable
```bash
# Run 1-Click Builder
Build_Shohoj_Macro_EXE.bat
# or
python build_exe.py
```

---

## ⌨️ Global Shortcuts & Controls

| Shortcut | Action | Description |
|:---:|:---:|---|
| <kbd>F8</kbd> | **Start / Stop Recording** | Captures clicks, typing, and mouse movements live into the timeline. |
| <kbd>F9</kbd> | **Play / Pause Macro** | Starts or pauses playback with active loop counter. |
| <kbd>F10</kbd> | **Emergency Kill Switch** | Instantly terminates macro execution at the kernel level. |
| **Mouse Corner** | **Panic Abort** | Move the physical mouse violently to the top-left $(0, 0)$ corner to abort. |
| <kbd>Delete</kbd> | **Delete Selected Steps** | Deletes all highlighted actions simultaneously (supports multi-selection). |
| <kbd>Ctrl</kbd> + <kbd>A</kbd> | **Select All** | Selects all rows in the timeline table. |
| <kbd>Ctrl</kbd> + <kbd>D</kbd> | **Duplicate Action** | Duplicates selected macro steps. |

---

## 📖 Complete User Guide

For detailed walkthroughs on CSV form automation, visual anchor snipping, and browser companion configuration, read the full [User Guide](docs/USER_GUIDE.md).

### 🛠️ Example: Auto-Filling Registration Forms with CSV
1. Open the **`📊 CSV Data`** tab in the left sidebar.
2. Click **`[📁 Load CSV Dataset]`** and select your `users.csv` file.
3. In the timeline, add a `Text Type` action and set text to `"{{first_name}} {{last_name}}"`.
4. Add a `Key Press` action for `<Tab>`, followed by another `Text Type` for `"{{email}}"`.
5. Press <kbd>F9</kbd> (Play): Shohoj Macro will fill **Row 1**, submit, then automatically loop through all rows in your dataset!

### 🎯 Example: Self-Adjusting Button Clicking with Image Anchors
1. In the timeline toolbar, click **`[📸 Snip Anchor]`**.
2. The screen freezes: drag a box around any button or icon on your screen.
3. Name the anchor (e.g. `submit_button`) and set confidence to `85%`.
4. Even if the window is moved to another monitor or scrolled, Shohoj Macro will scan the screen in $< 2\text{ms}$, locate the button, and auto-adjust its click directly on target.

---

## 🌐 Chrome / Edge Companion Setup

1. Open Google Chrome or Microsoft Edge and navigate to `chrome://extensions`.
2. Toggle on **Developer mode** in the top-right corner.
3. Click **Load unpacked** in the top-left.
4. Select the [`browser_extension`](browser_extension/) folder from this repository.
5. In Shohoj Macro Studio, click **`[🔍 Pick Web Element via Browser]`** to hover and capture web elements with 1-click ease!

---

## 📁 Repository Structure

```
shohojmacro/
├── assets/                       # Custom cyber-cyan application icons & graphics
├── browser_extension/            # Chrome/Edge Manifest V3 Companion Extension
│   ├── manifest.json
│   ├── background.js             # Keepalive worker & WebSocket bridge client
│   ├── content.js                # Stealth DOM hover inspector & screen coordinate mapper
│   └── popup.html / popup.js
├── docs/                         # In-depth architectural & user documentation
│   ├── USER_GUIDE.md             # Master step-by-step user guide & tutorials
│   └── ARCHITECTURE.md           # Low-level Win32, CV, and kinematic mathematics
├── shohoj_macro/                 # Core Python Package
│   ├── core/
│   │   ├── cv_engine.py          # Fast OpenCV multi-scale template matcher (<2ms)
│   │   ├── csv_engine.py         # UTF-8/BOM CSV dataset manager & {{variable}} interpolator
│   │   ├── humanizer.py          # Minimum-Jerk splines & 8-12Hz physiological rest tremors
│   │   ├── stealth_core.py       # Zero-GC streaming trajectory buffers & Gaussian hold times
│   │   ├── bio_rhythm.py         # Cognitive pauses & human session fatigue modeling
│   │   ├── recorder.py           # High-precision input recorder with hotkey suppression
│   │   ├── player.py             # Sub-ms multi-threaded playback engine with frame guards
│   │   ├── events.py             # Complete MacroEvent AST with Base64 image embedding
│   │   ├── storage.py            # .shj single-file portable JSON manager
│   │   ├── exporter.py           # Exporters to standalone Python (.py) and AutoHotkey (.ahk)
│   │   └── hotkeys.py            # Global low-level hotkey manager
│   ├── gui/
│   │   ├── app.py                # Main Apple Glassmorphism Studio window
│   │   ├── dynamic_island.py     # Windows 11 DWM anti-aliased floating Dynamic Island HUD
│   │   ├── image_snipper.py      # Interactive freeze-frame screen snipping tool
│   │   ├── csv_dock.py           # CSV data dock panel, data previewer & variable badges
│   │   ├── timeline_table.py     # Interactive action timeline with multi-selection & tooltips
│   │   ├── trajectory_canvas.py  # Live radar map displaying mouse paths and Bézier curves
│   │   ├── screen_overlay.py     # Zone Sniper 8x magnification loupe & circle drawer
│   │   └── glass_theme.py        # Liquid Obsidian theme tokens & GlassTooltip widgets
│   ├── utils/
│   │   ├── win32_capture.py      # Fast Win32 GDI Memory DC screen capture (<1.5ms)
│   │   ├── win32_input.py        # Hardware SendInput (ScanCodes), MapVirtualKeyW, DWM helpers
│   │   ├── timer.py              # Windows Multimedia Timer (winmm.timeBeginPeriod) wrapper
│   │   ├── dpi_helper.py         # Per-Monitor DPI Awareness V2 context manager
│   │   └── path_simplify.py      # Ramer-Douglas-Peucker (RDP) trajectory compression
│   └── version.py                # Version & developer metadata
├── tests/                        # 21 Automated Unit Tests (100% Passing)
├── build_exe.py                  # PyInstaller automated build script
├── Build_Shohoj_Macro_EXE.bat    # 1-Click EXE compiler
├── Launch_Shohoj_Macro.bat       # 1-Click Application Launcher
├── Launch_Silent.vbs             # 0-Console Silent Background Launcher
├── requirements.txt              # Python package requirements
└── README.md                     # Project documentation
```

---

## 🧪 Automated Test Suite

Shohoj Macro includes 21 comprehensive automated unit tests covering all core modules:
```bash
python run_tests.py
```
**Output:**
```
Ran 21 tests in 0.089s
OK - All automated tests passed successfully!
```

---

## 📄 License & Attribution

Distributed under the **MIT License**. See `LICENSE` for more information.

- **Author / Developer:** [Polash Khan](https://github.com/ypolash) (`ypolash` / `ypolash2`)
- **Project Link:** [https://github.com/ypolash/shohojmacro](https://github.com/ypolash/shohojmacro)
- **Dedication:** Built with pride for developers, gamers, and productivity power-users seeking effortless, undetectable automation.
