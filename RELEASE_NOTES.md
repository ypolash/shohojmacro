# ⚡ Shohoj Macro v2.7.0 (Enterprise Dual-Strategy NST & Auto-Updater Release)

> **Autonomous Stealth Automation, Dual-Strategy NST Browser Engine, Remote Auto-Updater & CSV Data Engine for Windows**  
> *Developed by [Polash Khan](https://github.com/ypolash) (`@ypolash`)*

---

## 📦 Downloads & Packages

| Package | File | Description |
|---|---|---|
| 💻 **Standalone Desktop Application** | **[`ShohojMacro-v2.7.0-Windows-x64.zip`](https://github.com/ypolash/shohojmacro/releases/download/v2.7.0/ShohojMacro-v2.7.0-Windows-x64.zip)** | Complete portable app for Windows 10 & 11. **No Python or dependencies needed — ready to run!** |
| 🌐 **Browser Companion Extension** | **[`ShohojCompanion-Extension-v2.7.0.zip`](https://github.com/ypolash/shohojmacro/releases/download/v2.7.0/ShohojCompanion-Extension-v2.7.0.zip)** | Chrome & Edge Manifest V3 extension for 1-click DOM element picking and stealth hardware click bridge. |

---

## 🌟 Key Highlights & Features in v2.7.0

### 🚀 1. Dual-Strategy NST Browser Controller
- **Strategy A (Local REST API):** High-speed, invisible profile search, proxy assignment, and remote debugger port resolution via NST Local API (`http://localhost:8848`).
- **Strategy B (Win32 Visual Fallback):** Automatic Win32 focus and physical search fallback if the NST API is unauthenticated or fails.
- **Dynamic Profile Search Column:** Configure default lookup column headers (e.g., `Email`, `Username`, `User`, `Profile ID`) directly in Settings.
- **Safe URL Encoding & Substring Matcher:** RFC-compliant URL parameter encoding for emails containing special characters (`+`, `&`) with intelligent substring profile matching.
- **Auto-Close Profile Teardown:** Automatically closes active browser profiles on row completion to prevent RAM and debugging port leaks.

### ⚡ 2. 1-Click Remote Auto-Updater
- **GitHub Release Integration:** Automatically queries GitHub Releases API on startup to detect newer versions.
- **1-Click Auto-Update Flow:** Displays release release notes and downloads/installs update zips seamlessly without manual re-installation.
- **Live Connection Diagnostics:** Test NST Local API connection status instantly from Settings -> Proxy & Browser.

---

# ⚡ Shohoj Macro v2.0.0 (Enterprise Stealth & Data Edition)

## 🌟 Key Highlights & Features in v2.0.0

### 📸 1. Zero-AI Visual Frame Synchronization & Auto-Adjusting Anchors
- **Freeze-Frame Screen Snipper:** Click `[📸 Snip Anchor]` to crop any button or UI element directly from your screen.
- **Dynamic Auto-Adjusting Clicks:** Uses high-speed OpenCV template matching ($< 2\text{ms}$) to find the button and **auto-adjusts the mouse click directly on it even if the window moved, resized, or scrolled!**
- **Visual State Guards:** Actions to `Wait Until Frame Appears` or `Wait Until Loading Spinner Disappears`.
- **100% Single-File Portability:** All template snippets are embedded as Base64 strings inside `.shj` files.

### 📊 2. Dynamic CSV Data-Driven Input Engine (Form Automation)
- **CSV Data Dock:** Load any CSV/Excel dataset (`users.csv`) with automatic encoding detection (`utf-8-sig`, `latin-1`).
- **Dynamic Variable Templating:** Type `"Hello {{first_name}}"` ➔ Tab ➔ `"{{email}}"`.
- **Batch Multi-Row Iteration:** Fills and submits Row 1, then automatically loops through Row 2, Row 3, ..., through all $N$ rows!

### 🪟 3. Flawless Apple Dynamic Island HUD (Windows 11 DWM Anti-Aliased)
- Silky-smooth 60fps pill HUD floating at the top of your screen with **0 black border artifacts**.
- **1-Click Studio Switcher:** Click `[🗖 Studio]` or the brand title on the floating HUD to instantly bring the main Studio window to the front.

### ⌨️ 4. 100% Hardware Scan-Code Precision
- Complete `VkKeyScanW` + `MapVirtualKeyW` hardware scan-code resolution with guaranteed $35\text{ms} - 55\text{ms}$ human hold times.
- React/Vue SPA-safe input streams (`Ctrl+A` ➔ `Backspace` ➔ type) to ensure single-page web apps never drop keystrokes.

### 🌿 5. Biomechanical Kinematics & Slow Organic Wandering
- **Quintic Minimum-Jerk Splines ($10t^3 - 15t^4 + 6t^5$):** Smooth Fitts's Law acceleration and deceleration curves without robotic jerkiness.
- **8–12Hz Physiological Rest Tremors:** Injects genuine harmonic micro-tremors ($\pm 0.2\text{px} - 0.4\text{px}$) that pass deep anti-cheat heuristic inspections.
- **`HUMAN_WANDER_SLOW`:** Gentle reading presence and natural hand resting for anti-AFK stealth.

### 🛡️ 6. Undetectable Chrome/Edge Companion Bridge
- Out-of-band communication over a local WebSocket (`ws://127.0.0.1:8765`).
- Triggers true physical OS hardware clicks with **`event.isTrusted === true`**, effortlessly bypassing Cloudflare Turnstile, DataDome, and anti-bot scripts.

---

## 🧪 Verification & Test Suite
- **21 / 21 Automated Unit Tests Passed** in 0.089s (100% Success).

---

## 🚀 How to Run

1. Download **`ShohojMacro-v2.0.0-Windows-x64.zip`** and extract it.
2. Double-click **`ShohojMacro.exe`** or **`Launch_Shohoj_Macro.bat`**.
3. Enjoy simple, intelligent, undetectable automation!
