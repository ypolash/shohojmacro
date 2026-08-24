# 📖 Shohoj Macro v2.0.0 — Comprehensive User Guide

**Developer:** [Polash Khan](https://github.com/ypolash) (`ypolash` / `ypolash2`)  
**Application:** Shohoj Macro ("সহজ ম্যাক্রো")

---

## 📑 Table of Contents
1. [Introduction & Interface Tour](#1-introduction--interface-tour)
2. [Workflow 1: Quick Record, Edit & Replay](#2-workflow-1-quick-record-edit--replay)
3. [Workflow 2: Dynamic CSV Form & Registration Automation](#3-workflow-2-dynamic-csv-form--registration-automation)
4. [Workflow 3: Self-Adjusting Click Targets with Visual Anchors](#4-workflow-3-self-adjusting-click-targets-with-visual-anchors)
5. [Workflow 4: Visual Frame Synchronization (State Guards)](#5-workflow-4-visual-frame-synchronization-state-guards)
6. [Workflow 5: Undetectable Web Automation via Chrome Companion](#6-workflow-5-undetectable-web-automation-via-chrome-companion)
7. [Workflow 6: Standalone Python & AutoHotkey Export](#7-workflow-6-standalone-python--autohotkey-export)
8. [Humanizer Physics & Anti-Detection Tuning](#8-humanizer-physics--anti-detection-tuning)
9. [Panic Fail-Safes & Troubleshooting](#9-panic-fail-safes--troubleshooting)

---

## 1. Introduction & Interface Tour

When you launch Shohoj Macro Studio, you are greeted by an **Apple-style Liquid Obsidian Glassmorphism Studio**:

- **Top Control Ribbon:**
  - **`● Record (F8)`**: Starts/stops global recording. Automatically suppresses trigger hotkeys from the timeline.
  - **`▶ Play (F9)`**: Starts/pauses playback.
  - **`⏹ Stop (F10)`**: Emergency stop / aborts playback.
  - **`Mode Selector`**: Choose `Clicks & Keys (Clean)` (recommended for snappy macros), `All Motion` (full cursor trails), or `Keys Only`.
  - **`Loops`**: Set number of repetitions ($1$ = single run, $0$ = infinite loop until stopped).
  - **`Speed Slider`**: Real-time multiplier ($0.2\times$ to $3.0\times$).
  - **`Humanize Switch`**: Toggles Minimum-Jerk kinematics, 8–12Hz resting tremors, and Gaussian click scatter.
  - **`🏝️ Mini HUD`**: Toggles the floating Dynamic Island HUD capsule.
- **Left Sidebar Tabs:**
  - **`📁 Library`**: Organize, search, and load your saved `.shj` macros.
  - **`📊 CSV Data`**: Upload CSV datasets, preview rows, and inspect dynamic variable badges (`{{col_name}}`).
- **Center Timeline Table:**
  - View, reorder, edit, duplicate, and toggle actions with multi-selection support (Shift+Click, Ctrl+Click, <kbd>Ctrl+A</kbd>).
  - Search filter bar to quickly find steps in long sequences.
  - **`[📸 Snip Anchor]`**: Freeze the screen and crop visual button templates.
- **Right Panel:**
  - **`Trajectory Canvas`**: Live radar map displaying mouse travel paths and Bézier curves.
  - **`Browser Companion Panel`**: Status indicator and 1-click DOM element inspector for Chrome/Edge.
  - **`Execution Log`**: Real-time ring-buffered activity log.

---

## 2. Workflow 1: Quick Record, Edit & Replay

1. **Start Recording:**
   - Press <kbd>F8</kbd> or click **`● Record (F8)`**.
   - The **Dynamic Island HUD** automatically floats to the top of your screen pulsing red: `● RECORDING (0 actions)`.
2. **Perform Actions:**
   - Click, type, and navigate naturally. Every step appears **live row-by-row** in the timeline table.
3. **Stop Recording:**
   - Press <kbd>F8</kbd> or click **`⏹ Stop Rec (F8)`**. Notice that <kbd>F8</kbd> is automatically excluded from your macro steps!
4. **Edit the Sequence:**
   - **Delete unwanted steps:** Highlight rows and press <kbd>Delete</kbd>.
   - **Adjust Delays:** Double-click any row or right-click ➔ `Adjust Delay...` to fine-tune pauses.
   - **Duplicate Steps:** Select rows and press <kbd>Ctrl+D</kbd>.
5. **Replay:**
   - Press <kbd>F9</kbd> to start playback. The Dynamic Island HUD pulses green displaying the active loop and step progress.

---

## 3. Workflow 2: Dynamic CSV Form & Registration Automation

Shohoj Macro can automatically read rows from an Excel or CSV file and fill hundreds of web or desktop forms automatically.

### Step-by-Step Setup:
1. **Prepare your CSV File (`users.csv`):**
   ```csv
   first_name,last_name,email,username,password
   Alice,Smith,alice@example.com,asmith,SecretPass1!
   Bob,Jones,bob@example.com,bjones,SecretPass2!
   Charlie,Brown,charlie@example.com,cbrown,SecretPass3!
   ```
2. **Load CSV into Shohoj Macro:**
   - Click the **`📊 CSV Data`** tab on the left sidebar.
   - Click **`[📁 Load CSV Dataset]`** and select `users.csv`.
   - Shohoj Macro detects the headers and creates clickable variable badges: `{{first_name}}`, `{{last_name}}`, `{{email}}`, etc.
   - The loop count automatically sets to the number of rows in your CSV ($3$).
3. **Add Templated Actions in Timeline:**
   - Add a `Text Type` action with text: `"{{first_name}}"`
   - Add a `Key Press` action: `<Tab>`
   - Add a `Text Type` action with text: `"{{last_name}}"`
   - Add a `Key Press` action: `<Tab>`
   - Add a `Text Type` action with text: `"{{email}}"`
   - Add a `Key Press` action: `<Enter>`
   - Add a `Delay` action: `1500ms` (for form submission)
4. **Run:**
   - Press <kbd>F9</kbd>. Loop 1 fills Alice's data, submits, then Loop 2 automatically fills Bob's data, followed by Charlie!

---

## 4. Workflow 3: Self-Adjusting Click Targets with Visual Anchors

Traditional macros click fixed $(X, Y)$ screen pixels. If a window moves, resizes, or scrolls, fixed clicks click the wrong spot. **Visual Anchors solve this completely without AI.**

1. Click **`[📸 Snip Anchor]`** in the timeline toolbar.
2. Your screen freezes with a crosshair cursor.
3. Drag a box around the button or icon you want to target (e.g. "Save", "Submit", or an in-game inventory item).
4. Enter a name (e.g. `save_button`) and set match confidence (default: `85%`).
5. A new `📸 Visual Anchor Click` step is added to your timeline with the template image embedded directly as Base64.
6. **During Playback:** Shohoj Macro scans the screen in $< 2\text{ms}$, finds where the button currently is on screen, and **auto-adjusts the mouse click directly on target** even if the window shifted!

---

## 5. Workflow 4: Visual Frame Synchronization (State Guards)

When automating slow websites, loading animations, or asynchronous workflows, fixed delays can cause failures. Use **Visual State Guards** to wait for frames dynamically:

- **Wait Until Frame Appears (`WAIT_UNTIL_FRAME_APPEARS`):**
  - Pauses execution until a specific visual badge appears (e.g. "Payment Confirmed", "Dashboard Ready").
  - Includes configurable timeout (e.g. `10s`). If the frame appears in 1.2s, it resumes *immediately* without wasting time!
- **Wait Until Frame Disappears (`WAIT_UNTIL_FRAME_DISAPPEARS`):**
  - Waits until a loading spinner, progress bar, or modal dialog completely vanishes before executing the next action.

---

## 6. Workflow 5: Undetectable Web Automation via Chrome Companion

1. **Install Companion Extension:**
   - Open `chrome://extensions` in Chrome or Edge.
   - Enable **Developer mode** ➔ Click **Load unpacked** ➔ Select [`browser_extension`](../browser_extension/).
2. **Inspect & Snip Web Elements:**
   - In Shohoj Macro Studio, click **`[🔍 Pick Web Element via Browser]`**.
   - Hover over any element in your browser ➔ The element highlights in cyan.
   - Click it ➔ Shohoj Macro captures its exact screen coordinates and CSS selector into your timeline.
3. **True Hardware Clicks (`isTrusted = true`):**
   - When played, Shohoj Macro triggers real OS kernel hardware events via `SendInput`. Cloudflare, DataDome, and anti-bot scripts treat it as a genuine human user touching a physical mouse.

---

## 7. Workflow 6: Standalone Python & AutoHotkey Export

Want to run your macro on a server or without the GUI?
1. Click **`[📤 Export]`** in the top ribbon.
2. Select your desired format:
   - **`Python (.py)`**: Generates a self-contained Python script with embedded WindMouse spline mathematics and sub-millisecond timer loops.
   - **`AutoHotkey (.ahk)`**: Generates clean, commented AutoHotkey v1/v2 code.
3. Save the script anywhere and run it independently!

---

## 8. Humanizer Physics & Anti-Detection Tuning

Shohoj Macro includes state-of-the-art biological kinematics to pass anti-cheat and anti-bot inspections:

- **Quintic Minimum-Jerk Splines ($10t^3 - 15t^4 + 6t^5$):** Emulates human motor control with zero endpoint acceleration and peak smooth velocity in the middle.
- **8–12Hz Physiological Tremor:** Simulates the continuous sub-pixel resting tremor of human hands.
- **Gaussian Click Scatter:** Clicks inside target zones cluster with 2D Gaussian density ($\sigma = R/3$), matching human finger tap dispersion.
- **`HUMAN_WANDER_SLOW`:** Simulates natural reading gaze or hand resting across a screen area.
- **Human Scroll Peek:** Smoothly scrolls down to simulate reading, pauses for inspection, and scrolls back the exact opposite distance for **net zero displacement**.

---

## 9. Panic Fail-Safes & Troubleshooting

### 🛑 Emergency Stop Options:
- **Global Hotkey:** Press <kbd>F10</kbd> at any time to instantly kill macro playback.
- **Mouse Corner Panic:** Move the physical mouse cursor violently to the top-left $(0, 0)$ corner of your monitor. The playback engine will halt immediately.

### ❓ Frequently Asked Questions:
- **Why are my clicks missing inside an Admin app (e.g. Task Manager / Game)?**
  - Windows UIPI (User Interface Privilege Isolation) prevents standard apps from controlling elevated windows. Right-click `ShohojMacro.exe` and select **"Run as Administrator"**.
- **Can I run macros without the Chrome extension?**
  - **Yes!** The desktop software is 100% standalone. The extension is only an optional companion for 1-click web DOM inspection.
