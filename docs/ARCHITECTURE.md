# 🏗️ Shohoj Macro v2.0.0 — System Architecture & Engineering Deep-Dive

**Developer:** [Polash Khan](https://github.com/ypolash) (`ypolash` / `ypolash2`)  
**Application:** Shohoj Macro ("সহজ ম্যাক্রো")

---

## 🔬 Architectural Overview

Shohoj Macro is structured into modular layers designed for **sub-millisecond timing precision**, **100% hardware driver legitimacy**, **sub-pixel computer vision**, and **undetectable biological kinematics**.

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                      APPLICATION LAYER (GUI / CLI)                     │
  │   ShohojMacroStudio • DynamicIslandHUD • ScreenSnipper • CSVDock       │
  └──────────────────────────────────┬─────────────────────────────────────┘
                                     │
  ┌──────────────────────────────────▼─────────────────────────────────────┐
  │                        CORE EXECUTION ENGINES                          │
  │   MacroPlayer • MacroRecorder • CVTemplateMatcher • CSVDataEngine      │
  │   HumanizerEngine • StealthCore • BioRhythmEngine • Storage/Exporter   │
  └──────────────────────────────────┬─────────────────────────────────────┘
                                     │
  ┌──────────────────────────────────▼─────────────────────────────────────┐
  │                      WIN32 LOW-LEVEL HARDWARE DRIVERS                  │
  │   win32_input (SendInput ScanCodes) • win32_capture (GDI BitBlt)       │
  │   timer (timeBeginPeriod 1ms) • dpi_helper (Per-Monitor DPI V2)        │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Win32 Low-Level Hardware Input Layer

Standard automation libraries (PyAutoGUI, standard Python `keyboard` library) inject virtual key events (`KEYBDINPUT.wVk`) without scan codes. DirectInput games and secure Windows apps ignore virtual key events because they lack real hardware signals.

### Complete Hardware ScanCode Resolution:
Shohoj Macro uses `user32.VkKeyScanW` + `user32.MapVirtualKeyW`:
1. Resolves ASCII/Unicode characters into virtual keys and scan codes.
2. Directs `user32.SendInput` using `KEYEVENTF_SCANCODE` (`INPUT_KEYBOARD.union.ki.wScan`).
3. Enforces a Gaussian human hold duration ($35\text{ms} \pm 10\text{ms}$) with sub-millisecond precision.

---

## 2. High-Speed Screen Capture & Zero-AI Computer Vision

### Win32 GDI Memory DC Capture:
Traditional PIL `ImageGrab.grab()` incurs heavy overhead ($40\text{ms} - 80\text{ms}$ on 4K screens). Shohoj Macro implements `win32_capture.py` directly calling unmanaged GDI APIs:
- `CreateCompatibleDC(h_desktop)`
- `CreateCompatibleBitmap(h_desktop, width, height)`
- `BitBlt(h_capture_dc, 0, 0, w, h, h_desktop, left, top, SRCCOPY)`
- `GetDIBits(...)` directly into an unmanaged memory buffer.
- Latency is reduced to **$< 1.5\text{ms}$**.

### Multi-Scale Pyramid Matching:
Template matching uses normalized cross-correlation:
$$R(x, y) = \frac{\sum_{x', y'} (T(x', y') \cdot I(x+x', y+y'))}{\sqrt{\sum_{x', y'} T(x', y')^2 \cdot \sum_{x', y'} I(x+x', y+y')^2}}$$

If the initial $1.0\times$ match score is below threshold, the engine evaluates multi-scale pyramid matrices ($[0.9\times, 1.0\times, 1.1\times, 1.25\times]$) to handle DPI scaling and browser zoom variance seamlessly.

---

## 3. Biomechanical Human Kinematics

### Quintic Minimum-Jerk Spline Formulation:
Human limb movements minimize the derivative of acceleration (jerk):
$$x(t) = x_0 + (x_f - x_0) \cdot (10t^3 - 15t^4 + 6t^5)$$
where $t \in [0, 1]$. This produces zero velocity and zero acceleration at endpoints, with smooth peak velocity in the middle matching Fitts's Law.

### 8–12Hz Physiological Rest Tremor:
Real human hands exhibit an involuntary resting micro-tremor between 8Hz and 12Hz. Shohoj Macro injects harmonic sine waves scaled by the velocity bell-curve:
$$T(t) = \left(\sin(2\pi f_1 t) + 0.5\cos(2\pi f_2 t)\right) \cdot \text{scale} \cdot \sin(\pi t)$$
where $f_1 \in [8.0, 10.0]\text{Hz}$ and $f_2 \in [10.5, 12.5]\text{Hz}$.

---

## 4. Single-File Portability (`.shj` Embedded Base64)

Macro `.shj` files use structured JSON AST with embedded Base64 PNG assets:
```json
{
  "header": {
    "app": "Shohoj Macro",
    "version": "2.0.0",
    "file_format": "2.0",
    "author": "Polash Khan (ypolash2)"
  },
  "events": [
    {
      "id": "e4f8a1bc",
      "event_type": "visual_anchor_click",
      "template_name": "submit_btn",
      "template_base64": "iVBORw0KGgoAAAANSUhEUgAAADIA...",
      "confidence_threshold": 0.85,
      "delay_after_ms": 200.0
    }
  ]
}
```
This guarantees that copying a single `.shj` file to any computer immediately loads all visual templates with zero broken file paths.
