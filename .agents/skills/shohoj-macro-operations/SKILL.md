---
name: shohoj-macro-operations
description: Protocol, standards, and architecture for Shohoj Macro Studio bulk data execution, semi-automated forms, circuit-breaker safety, and UI/UX state management.
---

# Shohoj Macro Operations Architecture & Protocol

This skill codifies the core architecture, error prevention protocols, and UI state rules for **Shohoj Macro Operations Studio** and the **AI Orchestrator Engine**.

---

## 1. The 4-Phase Bulk Execution Loop

When executing a macro against an Excel (`.xlsx`) or CSV (`.csv`) dataset, the engine must proceed through four distinct phases for every row:

```
[Row N] ──► Phase 1: Data Interpolation (Replace {{Col}} with row values)
         ──► Phase 2: Pre-Flight Health Check (Verify CDP / Window readiness)
         ──► Phase 3: Macro Playback (Execute clicks, typing, visual anchors)
         ──► Phase 4: Semi-Automated Gate / Auto-Advance (Pause & chime if semi-auto)
```

### Critical Rules for Phase Execution:
1. **Never Blindly Advance on Connection Failure (Circuit Breaker)**:
   - If an `ECONNREFUSED`, `ConnectionRefusedError`, `TargetClosedError`, or missing browser port occurs, **IMMEDIATELY ABORT** the entire bulk execution loop.
   - **NEVER** increment `curr_row += 1` on a connection drop. Doing so cascades failures and ruins hundreds of rows in seconds.
2. **Semi-Automated Error Pausing**:
   - In Semi-Automated mode, if a step fails on Row $N$ (e.g. element not found or page timeout), the bot must **PAUSE** and sound an alert chime.
   - Give the user the opportunity to complete the step manually or press `F9 (Mark Done & Next)` or `Stop`. Never silently skip to the next row.
3. **Target URL Optionality**:
   - `Target URL` must NEVER be strictly mandatory. If blank, macro playback executes directly on whatever window or browser tab the user has currently focused in the foreground.

---

## 2. Dynamic UI/UX State Machine

The Operations Studio Panel (`operation_panel.py`) must maintain a live, reactive state machine synchronized with background threads:

| State | Status Badge | Start Button | Stop Button | Mark Done Button |
| :--- | :--- | :--- | :--- | :--- |
| **`IDLE`** | `● IDLE` (Dark Slate) | `[ 🚀 Start Bulk Execution ]` (Bright Cyan `#00F0FF`, Active) | `[ ⏹ Stop ]` (Disabled / Subdued) | `[ ✅ Mark Done & Next (F9) ]` (Normal) |
| **`RUNNING`** | `🟢 RUNNING - Row X of Y` (Emerald `#30D158`) | `[ ⏳ Running Row X/Y... ]` (Disabled, Navy `#1A2D40`) | `[ ⏹ STOP OPERATION ]` (Active, Vibrant Crimson `#FF3B30`, White text) | Disabled |
| **`WAITING_MANUAL`** | `🔔 WAITING FOR YOU - Row X` (Amber `#FF9F0A`) | `[ ⏸️ Paused for Manual Step ]` (Disabled) | `[ ⏹ STOP OPERATION ]` (Active) | `[ 👉 CLICK: Mark Done (F9) ]` (Pulsing Green `#30D158`, High Contrast) |
| **`STOPPED`** | `⏹ STOPPED` (Muted Red) | Resets to `[ 🚀 Start Bulk Execution ]` | Resets to default | Resets to default |

All state transitions must be dispatched thread-safely via `master.after(0, ...)`.

---

## 3. Macro Template Management

1. **Clear / Deselect Capability**:
   - Any panel or dialog that loads a macro template must provide a visible, one-click `[ ✖ Clear ]` button.
   - Clearing resets the selected path, resets UI labels to `No Macro Loaded`, and flushes persisted memory in `SettingsManager`.
2. **Visual Contrast Standards**:
   - Never place red text on a dark red background. Buttons like `● Record Macro` must use high-contrast styling (e.g., `#7A1C24` background with crisp `#FFFFFF` bold text).

---

## 4. Multi-Targeting Fallback Hierarchy

Shohoj Macro supports three input targeting strategies with seamless fallback:
1. **🌐 Browser DOM / CDP**: High precision via `#id`, `.class`, or CSS selectors. Requires active CDP or Browser Extension. If disconnected, gracefully prompt user and clear stale ports.
2. **📸 Zero-AI Visual Anchors**: Screen cropping via `[📸 Snip Anchor]`. Works across all native Windows applications and browsers without plugins.
3. **⌨️ Clean Physical Coordinates**: Direct Win32 hardware `SendInput` in `Clicks & Keys (Clean)` mode. Zero dependency on web drivers.

---

## 5. Direct CDP DOM Execution & Disposable Overlay Protocol

When interacting with web element selectors (`CDP_PHYSICAL_INPUT`):
1. **Zero Screen Coordinate Translation**:
   - Never convert CSS selectors to physical Windows mouse coordinates (`SetCursorPos`). Windows DPI scaling (125%/150%) and page scrolling cause severe offset drift.
   - Always execute directly via Playwright's `locator.scroll_into_view_if_needed()`, `locator.click()`, and `locator.fill()`.
2. **Disposable Overlay Auto-Bypass**:
   - Cookie banners (`#onetrust-accept-btn-handler`, `cookie`, `consent`, `gdpr`), newsletter modals, and promotional alerts only exist once per session.
   - When missing or marked `error_policy: skip`, the engine must skip gracefully in $<0.1$s and immediately continue form filling without waking Idle Guardian or failing the run.
3. **Native `<select>` Handling**:
   - HTML `<select>` elements must be chosen using `locator.select_option(label=text)` rather than simulated keyboard typing.
