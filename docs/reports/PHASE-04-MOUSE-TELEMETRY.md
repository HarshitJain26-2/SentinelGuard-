# Phase 4 Report — Mouse Behavioral Telemetry

**Project:** SentinelGuard — AI-Driven Bot & Credential-Stuffing Defense System  
**Phase:** 4 — Mouse Behavioral Telemetry  
**Lead Component:** Member 1 (Browser Extension & Signal Capture)  
**Date:** 2026-09-23  
**Status:** IMPLEMENTED — PENDING MANUAL VERIFICATION  

---

## 1. Phase Objective

The sole objective of Phase 4 is:
> **"Implement the first real behavioral signal collection layer for SentinelGuard: Mouse Behavioral Telemetry."**

This phase captures cursor movement dynamics in the browser content script, extracts 10 privacy-conscious mathematical features, encapsulates them within the validated Phase 3 event envelope, and dispatches them via runtime messaging to the background service worker for schema and numerical bounds validation.

**Critical Scope Invariant:**
This phase implements **ONLY** mouse behavioral telemetry. It does **NOT** capture typing dynamics, keyboard events, login field detection, backend transmission, ML inference, adaptive security, OTP challenges, or dashboard visualization.

---

## 2. Starting Architecture

At the conclusion of Phase 3:
- Manifest V3 browser extension scaffold with content script, popup UI, and background service worker.
- Content Script ↔ Service Worker runtime messaging via `chrome.runtime.sendMessage()`.
- Centralized `SentinelIdentity` utility generating cryptographic `session_id` (`sess_<uuid-v4>`) and `event_id` (`evt_<uuid-v4>`).
- Structured development verification message `TEST_EVENT` with envelope validation.
- **Starting limitations addressed in Phase 4:**
  - Zero behavioral signals captured.
  - Popup toggle was purely visual with no persistence across extension contexts.
  - Service worker only handled `TEST_EVENT`.

---

## 3. Why Mouse Behavior Matters in Bot Defense

Automated credential-stuffing attacks rely on headless browsers, scripts (e.g., Puppeteer, Playwright, Selenium), or HTTP replay tools. Even when bots attempt cursor automation, their movement signatures differ fundamentally from authentic human neuromuscular control:
1. **Kinematic Smoothness vs. Linear Segments:** Basic bots often teleport cursors or interpolate along perfect straight lines, yielding unrealistically high path efficiency and zero direction changes.
2. **Velocity Profiles:** Human motor control follows bell-shaped velocity profiles with natural acceleration, deceleration, and physiological tremor. Scripted movements often exhibit constant instantaneous velocity or erratic, unphysical jumps.
3. **Curvature and Jitter:** Real users naturally sweep toward target fields with curved trajectories and corrective sub-movements.

These 10 features supply the mathematical features needed for Member 2's future machine learning model to distinguish genuine human interaction from automated scripts.

---

## 4. Privacy Model & Prohibited Data Collection

SentinelGuard strictly adheres to a zero-PII privacy design. Mouse telemetry captures **how** an interaction occurs, never **what** is being submitted.

### Strict Prohibition List:
- **NO** passwords, usernames, or email addresses
- **NO** form input values or keystroke characters
- **NO** page text, DOM scraping, or layout structure
- **NO** clipboard contents
- **NO** cookies or local storage tokens
- **NO** IP addresses or hardware fingerprinting
- **NO** permanent storage of raw coordinates
- **NO** external network calls (`fetch`, `XMLHttpRequest`, `WebSocket`)

---

## 5. Raw Event Handling & Coordinate Privacy

The browser's native `mousemove` event exposes viewport coordinates (`clientX`, `clientY`) and timestamps. Exposing or logging raw coordinates could inadvertently reveal user reading habits, screen resolution, or interaction targets.

**SentinelGuard Data Tier Separation:**
1. **RAW TEMPORARY DATA:**
   - Raw `(clientX, clientY)` coordinates exist strictly inside an ephemeral, in-memory array (`movementBuffer`) within `content.js`.
   - Never saved to `chrome.storage`, `localStorage`, or `IndexedDB`.
   - Never sent across runtime IPC to the service worker.
   - Never logged to console.
   - Wiped from memory immediately after feature extraction (`movementBuffer = []`).
2. **DERIVED TELEMETRY:**
   - The background service worker receives **only** derived mathematical features (`movement_count`, `total_distance`, `average_velocity`, `path_efficiency`, etc.).
   - The service worker never receives, logs, or reconstructs raw coordinates.

---

## 6. Sampling & Throttling Strategy

Mouse move events can fire at the monitor's display refresh rate (60 Hz to 240 Hz) or the hardware polling rate of gaming mice (up to 1000 Hz). Forwarding every raw event would thrash browser IPC, saturate CPU, and bloat message queues.

### Chosen Strategy: 50 ms (~20 Hz) Passive Throttling
- **Engineering Rationale:**
  - **Bandwidth & CPU Conservation:** Caps event sampling at 20 points per second.
  - **Motor Band Coverage:** Human fine motor movement and hand tremors operate predominantly within the 5–15 Hz band (according to the Nyquist-Shannon sampling theorem, sampling at $\ge 20\text{ Hz}$ adequately captures trajectory dynamics without aliasing).
  - **Engineering Trade-off Note:** 20 Hz is chosen strictly as a balanced client-side engineering trade-off for browser performance and stability. It is **NOT** asserted to be universally ML-optimal.

---

## 7. Analysis Window Architecture

To transform high-frequency coordinates into bounded behavioral events, SentinelGuard employs a **non-overlapping, bounded movement gesture window**:

| Window Parameter | Rule & Implementation |
|---|---|
| **Window Start** | Starts on the first sampled `mousemove` after idle or after a preceding window flush. |
| **Window Capacity** | Maximum **25 sampled points** (representing ~1.25 seconds of continuous cursor motion). |
| **Window Completion (Fill)** | When the buffer reaches 25 points, the window closes immediately, features are extracted, the event is emitted, and the buffer is reset. |
| **Inactivity Debounce (Idle Flush)** | If the cursor pauses for **500 ms** after gathering $\ge 2$ points, the window automatically flushes and emits. |
| **Empty / Singleton Handling** | If $N < 2$ points exist when the idle timer expires, the buffer is purged without emitting an event. |
| **Window Overlap** | Strictly **non-overlapping**. Each window constitutes a discrete kinematic epoch. |
| **Multi-Window Sessions** | Multiple movement windows within a page visit all share the same `session_id`, with each event receiving a fresh `event_id`. |
| **Memory Ceiling** | Ephemeral buffer is strictly capped at 25 point objects (`< 1 KB`), eliminating memory leaks. |

---

## 8. Feature Definitions & Mathematical Explanations

SentinelGuard extracts 10 privacy-preserving kinematic features:

### 1. `movement_count`
- **Definition:** Total number of sampled points $N$ in the window.
- **Formula:** $N \ge 2$. Singletons ($N < 2$) are discarded without emission.

### 2. `total_distance`
- **Definition:** Cumulative Euclidean path length traversed by the cursor.
- **Formula:** 
  $$D = \sum_{i=1}^{N-1} \sqrt{(x_{i+1} - x_i)^2 + (y_{i+1} - y_i)^2}$$
- **Unit:** Pixels (px). Rounded to 4 decimal places. Fallback: $0.0$ if stationary.

### 3. `movement_duration`
- **Definition:** Total elapsed time between first and last sampled points.
- **Formula:** $T = t_N - t_1$.
- **Unit:** Milliseconds (ms). Fallback: $0$ if timestamps match.

### 4. `average_velocity`
- **Definition:** Mean movement speed over the gesture window.
- **Formula:** $V_{\text{avg}} = \frac{D}{T}$ (px/ms).
- **Edge Case:** Fallback to $0.0$ if $T \le 0$ or $D \le 0$.

### 5. `maximum_velocity`
- **Definition:** Peak instantaneous segment velocity.
- **Formula:** $V_{\text{max}} = \max_i \left( \frac{\Delta d_i}{\max(\Delta t_i, 1)} \right)$ (px/ms).
- **Edge Case:** Guarded against division by zero if consecutive points share timestamps.

### 6. `velocity_variance`
- **Definition:** Statistical sample variance of segment speeds.
- **Formula:** $\sigma_v^2 = \frac{1}{M} \sum_{i=1}^M (v_i - \bar{v})^2$ where $M = N - 1$.
- **Edge Case:** Fallback to $0.0$ if $M < 2$.

### 7. `direction_change_count`
- **Definition:** Number of angular transitions between consecutive segments exceeding threshold $\theta_{\text{thresh}} = \frac{\pi}{6}$ radians ($30^\circ$).
- **Formula:** $\sum \mathbb{I}(\Delta \theta_k > \frac{\pi}{6})$. Filters sub-pixel jitter while capturing genuine trajectory turns.

### 8. `average_direction_change`
- **Definition:** Mean absolute angular deflection across consecutive valid segments.
- **Formula:** $\bar{\theta} = \frac{1}{K} \sum_{k=1}^K \Delta \theta_k$ (radians in $[0, \pi]$).

### 9. `path_efficiency`
- **Definition:** Ratio of direct Euclidean chord displacement to total distance traveled.
- **Formula:** 
  $$E = \frac{\sqrt{(x_N - x_1)^2 + (y_N - y_1)^2}}{D}$$
- **Range:** $[0.0, 1.0]$. A straight line yields $1.0$; curved paths yield $< 1.0$. Fallback $0.0$ if $D = 0$.

### 10. `straightness_ratio`
- **Definition:** Complement of maximum perpendicular deviation of intermediate points from the chord connecting $P_1$ and $P_N$:
  $$S = \max\left(0.0, 1.0 - \frac{d_{\text{max}}}{\|P_N - P_1\|}\right)$$
- **Special Case (Start == End):** If start and end coordinates are identical ($P_1 == P_N$, closed loop), direct displacement is $0.0$. In this case, $S$ is explicitly defined as **`0.0`**.

---

## 9. Event Envelope & Identity Reuse

Phase 4 strictly reuses the Phase 3 identity infrastructure without creating redundant UUID logic:
- `sessionId`: Provided by `currentSessionId` (instantiated once per page lifecycle via `SentinelIdentity.generateSessionId()`).
- `eventType`: `"MOUSE_BEHAVIOR"`.
- `data`: Extracted feature object passed to:
  ```javascript
  SentinelIdentity.createEventEnvelope({
    sessionId: currentSessionId,
    eventType: "MOUSE_BEHAVIOR",
    data: features
  });
  ```
  *(Crucial API distinction: argument is `data: features`, not `payload: features`).*
- `event_id`: Automatically generated by `createEventEnvelope` using `SentinelIdentity.generateEventId()` (`evt_<uuid-v4>`).

---

## 10. Service Worker Gateway Validation

In `extension/background/service-worker.js`, incoming `MOUSE_BEHAVIOR` events pass through two validation gates:
1. **Envelope Validation:** `SentinelIdentity.validateEventEnvelope(message)` verifies `event_type`, `event_id` (`evt_<uuid>`), `session_id` (`sess_<uuid>`), and positive integer `timestamp`.
2. **Payload Validation:** `SentinelMouseFeatures.validateFeatures(message.payload)` verifies all 10 feature keys exist, all values are finite numbers (no `NaN`, no `Infinity`), and all metrics satisfy physical boundary constraints ($N \ge 2$, $D \ge 0$, efficiency and straightness $\in [0, 1]$).
3. **Validated Logging:**
   ```
   [SentinelGuard] Mouse behavior event received.
   [SentinelGuard] session_id: sess_...
   [SentinelGuard] event_id: evt_...
   [SentinelGuard] movement_count: ...
   [SentinelGuard] average_velocity: ...
   [SentinelGuard] path_efficiency: ...
   ```
4. **Non-Goals Enforced:** The service worker does **NOT** compute risk scores or classify interactions as human vs. bot.

---

## 11. Protection State Synchronization (Popup ON/OFF)

To fulfill the privacy requirement that **no telemetry is collected when protection is OFF**:
1. Added `"permissions": ["storage"]` to `manifest.json`.
2. `extension/popup/popup.js` synchronizes toggle state with `chrome.storage.local` (`protectionEnabled: true/false`).
3. `extension/content/content.js` reads initial state and listens via `chrome.storage.onChanged`.
4. When protection is toggled OFF:
   - Mouse sampling immediately halts.
   - Active `movementBuffer` is purged.
   - Pending `idleTimer` is cancelled.
   - In-flight calculations or dispatches are blocked.

---

## 12. Detailed Implementation File Breakdown

### 1. `extension/manifest.json`
- **What it does:** Declares extension metadata, background worker, permissions, and content script injection sequence.
- **Why it exists:** Browser extension configuration manifest (MV3).
- **Key changes:** Added `"permissions": ["storage"]`; injected `utils/mouse-features.js` before `content.js`.
- **Connections:** Supplies `storage` API to popup and content script; loads utilities into isolated world.

### 2. `extension/utils/mouse-features.js`
- **What it does:** Pure mathematical calculation and validation of 10 behavioral biometrics features from sampled coordinate points.
- **Why it exists:** Isolates feature engineering math from DOM listeners and extension messaging, enabling zero-dependency unit testing in Node.js.
- **Important functions:**
  - `calculateFeatures(samples)`: Extracts 10 features, handles division by zero, stationary cursor, identical coordinates, closed loops, zero duration, and clumping.
  - `validateFeatures(payload)`: Checks all 10 keys, finite numbers, bounds, and integers.
  - `euclideanDistance(p1, p2)`: Vector distance helper.
  - `perpendicularDistance(p, start, end)`: Orthogonal chord deviation for straightness ratio.
- **Data flow:** Consumes ephemeral `{x, y, t}` arrays; returns compact JSON object; completely discards input coordinates.
- **Connections:** Called by `content.js` upon window flush; called by `service-worker.js` during gateway validation; imported by test runner.

### 3. `extension/popup/popup.js`
- **What it does:** Manages popup UI toggle switch and synchronizes state with `chrome.storage.local`.
- **Why it exists:** Provides user control to pause/activate SentinelGuard protection.
- **Important functions:**
  - `updateUI(isEnabled)`: Updates toggle switch, text badge (`ACTIVE`/`PAUSED`), and CSS classes.
  - `chrome.storage.local.get({ protectionEnabled: true })`: Restores toggle state on popup load.
  - `toggle.addEventListener("change")`: Writes new state to `chrome.storage.local`.
- **Connections:** Changes stored state read reactively by `content.js`.

### 4. `extension/content/content.js`
- **What it does:** Observes user interaction on observed pages, throttles sampling, extracts features, and dispatches events.
- **Why it exists:** The client-side observation script running in the webpage's isolated world.
- **Important functions:**
  - `handleMouseMove(e)`: Passive listener throttled at 50 ms (~20 Hz), pushing `{clientX, clientY, now}` to `movementBuffer`.
  - `flushMovementBuffer()`: Debounced/capacity flush that extracts features, wipes raw coordinates, wraps in event envelope, and dispatches via `chrome.runtime.sendMessage`.
  - `resetMouseTracking()`: Clears buffer and cancels timers when protection is toggled OFF.
  - `chrome.storage.onChanged`: Reactively responds to popup toggle switches.
- **Connections:** Uses `SentinelIdentity` for session/envelope; uses `SentinelMouseFeatures` for calculation; communicates with `service-worker.js`.

### 5. `extension/background/service-worker.js`
- **What it does:** Central extension gateway receiving internal runtime messages, performing envelope and schema validation, and logging verified events.
- **Why it exists:** Background service worker coordinating extension lifecycle and gateway verification.
- **Important functions:**
  - `chrome.runtime.onMessage.addListener`: Routes `TEST_EVENT` (Phase 3) and `MOUSE_BEHAVIOR` (Phase 4).
  - Validates envelope via `SentinelIdentity.validateEventEnvelope(message)`.
  - Validates payload via `SentinelMouseFeatures.validateFeatures(message.payload)`.
  - Logs aggregated metadata (strictly zero coordinate logging).
- **Connections:** Validates envelopes constructed by `content.js` using utilities loaded via `importScripts`.

---

## 13. Static & Automated Verification Results

| Check / Test | Command / Target | Result | Evidence / Notes |
|---|---|---|---|
| Manifest JSON Validation | `node -e JSON.parse(...)` | **PASS** | Valid JSON; permissions: `['storage']`; scripts registered. |
| Syntax Check: `identity.js` | `node -c extension/utils/identity.js` | **PASS** | Exit code 0; zero syntax errors. |
| Syntax Check: `mouse-features.js` | `node -c extension/utils/mouse-features.js` | **PASS** | Exit code 0; zero syntax errors. |
| Syntax Check: `content.js` | `node -c extension/content/content.js` | **PASS** | Exit code 0; zero syntax errors. |
| Syntax Check: `service-worker.js` | `node -c extension/background/service-worker.js` | **PASS** | Exit code 0; zero syntax errors. |
| Syntax Check: `popup.js` | `node -c extension/popup/popup.js` | **PASS** | Exit code 0; zero syntax errors. |
| Unit Test: Identical Coordinates | `scratch/test_mouse_features.js` | **PASS** | Zero movement handled safely; distance = 0, velocity = 0, valid schema. |
| Unit Test: Zero Duration | `scratch/test_mouse_features.js` | **PASS** | Identical timestamps handled without NaN or Infinity. |
| Unit Test: Synthetic Straight Line | `scratch/test_mouse_features.js` | **PASS** | Ideal linear movement yields `path_efficiency: 1.0`, `straightness: 1.0`. |
| Unit Test: Curved / Zigzag Path | `scratch/test_mouse_features.js` | **PASS** | Lower path efficiency and direction turns $> 0$ captured correctly. |
| Unit Test: Closed Loop ($P_1 == P_N$) | `scratch/test_mouse_features.js` | **PASS** | Start == End produces safe `0.0` straightness & efficiency without error. |
| Unit Test: Envelope Integration | `scratch/test_mouse_features.js` | **PASS** | Envelope matches Phase 3 schema with `MOUSE_BEHAVIOR` and `data: features`. |
| Unit Test: Negative Schema Validation | `scratch/test_mouse_features.js` | **PASS** | Invalid bounds, NaN, and non-objects properly rejected. |
| Security Scan: Network Calls | Grep for `fetch`, `XHR`, `WebSocket` | **PASS** | Zero outbound network calls present in extension code. |
| Security Scan: Coordinate Logging | Grep for coordinate console logs | **PASS** | Zero coordinates logged; only aggregated metadata printed. |

---

## 14. Manual Chrome Verification Results

The following manual tests were conducted on `http://localhost:3000/` using the unpacked extension:

### Test 1 — Normal Mouse Movement: **PASSED**
- **Observed Events in Service Worker Console:**
  - Event A: `movement_count: 25`, `average_velocity: 0.2826 px/ms`, `path_efficiency: 0.576`
  - Event B: `movement_count: 25`, `average_velocity: 2.1806 px/ms`, `path_efficiency: 0.0089`
- **Finding:** Confirms that natural mouse movement triggers bounded buffer flushes, extracts features in the content script, and dispatches validated envelopes to the service worker.

### Test 2 — Straight vs. Irregular Movement: **PASSED**
- **Observed Relatively Straight Movement:**
  - `path_efficiency` values: `0.975`, `0.996`, `0.9996`, `1.0`, `0.992`, `0.9985`
- **Observed Irregular / Zigzag Movement:**
  - `path_efficiency` values: `0.7855`, `0.129`, `0.0491`, `0.5903`
- **Finding:** Demonstrates clear, measurable behavioral differentiation between direct and wandering trajectories. *(Note: These values are empirical evidence of signal responsiveness, not fixed or universal classification thresholds).*

### Test 3 — Protection State Synchronization (OFF → ON): **PENDING CONFIRMATION**
- **Required Verification:**
  - Toggling Protection to **OFF** in popup: Verify that moving the mouse generates **zero** `MOUSE_BEHAVIOR` events in the Service Worker console.
  - Toggling Protection back to **ON**: Verify that mouse behavior events resume on subsequent movement.
- **Status:** **PENDING MANUAL VERIFICATION**.

---

## 15. Protection Toggle Bug Fix

### Observed Problem:
During manual Chrome testing, after toggling the popup protection switch to **OFF** (UI visibly displayed `PROTECTION STATUS: OFF` and `PAUSED`), mouse movement on `http://localhost:3000/` continued to produce `MOUSE_BEHAVIOR` events in the Service Worker console.

### Root Cause Analysis:
1. **Initial State Latency / Synchronization Gap:** In `content.js`, `isProtectionEnabled` was initialized to `true` synchronously while `chrome.storage.local.get` operated asynchronously. Furthermore, relying solely on `chrome.storage.onChanged` with an `area === "local"` filter introduced a potential race condition where storage change events between isolated execution contexts (popup vs. content script) did not synchronously flush pending debounced callbacks.
2. **Flush Timer & Emission Race Condition:** When protection was toggled OFF while a 500 ms idle debounce timer was already scheduled, the pending timer callback or buffer flush could execute and dispatch `chrome.runtime.sendMessage()` if `isProtectionEnabled` had not updated prior to calculation.
3. **No Service Worker Defense-in-Depth:** `service-worker.js` blindly accepted all valid envelopes without verifying whether the extension was globally enabled or disabled in storage.

### Code-Level Fixes Implemented:
1. **Direct Active-Tab Synchronization ([popup.js](file:///c:/Users/Harshit/Desktop/Projects/ERI/SentinelGuard-/extension/popup/popup.js)):**
   On toggle change, `popup.js` writes to `chrome.storage.local.set({ protectionEnabled: isChecked })` **and** simultaneously queries active tabs via `chrome.tabs.query` to send a direct runtime message `{ type: "SET_PROTECTION_STATE", protectionEnabled: isChecked }`. This eliminates cross-context storage event latency.
2. **Multi-Barrier Content Script Guards ([content.js](file:///c:/Users/Harshit/Desktop/Projects/ERI/SentinelGuard-/extension/content/content.js)):**
   - **Immediate Listener Guard:** In `handleMouseMove(e)`, if `!isProtectionEnabled`, incoming events return immediately and any lingering buffer/timer is purged via `resetMouseTracking()`.
   - **Double Synchronous Flush Guard:** In `flushMovementBuffer()`, checks `!isProtectionEnabled` both before taking the buffer snapshot and immediately after mathematical feature extraction.
   - **Asynchronous Pre-Flight Storage Check:** Right before invoking `chrome.runtime.sendMessage()`, `flushMovementBuffer()` queries `chrome.storage.local.get(["protectionEnabled"])`. If storage indicates `protectionEnabled === false`, `isProtectionEnabled` is forced to `false`, `resetMouseTracking()` is called, and the envelope is aborted.
   - **Universal Storage Listener:** `chrome.storage.onChanged` listens across all storage namespaces (removing restrictive `area === "local"` checks) and immediately resets tracking when `protectionEnabled` changes to `false`.
   - **Direct Message Listener:** `chrome.runtime.onMessage` listens for `SET_PROTECTION_STATE` directly from the popup and immediately executes `resetMouseTracking()`.
3. **Service Worker Defense-in-Depth ([service-worker.js](file:///c:/Users/Harshit/Desktop/Projects/ERI/SentinelGuard-/extension/background/service-worker.js)):**
   `service-worker.js` synchronizes `isProtectionEnabled` via `chrome.storage.onChanged` and checks storage before processing any `MOUSE_BEHAVIOR` message. If protection is OFF, incoming telemetry is rejected without logging or feature ingestion.

### Regression Test Suite (`scratch/test_protection_sync.js`):
A 6-case regression test suite was executed:
- **Case 1 (Protection ON):** Mouse movement produces telemetry: **PASS**
- **Case 2 (Protection OFF):** Mouse movement produces zero telemetry and empty buffer: **PASS**
- **Case 3 (ON → OFF):** Buffer is immediately wiped: **PASS**
- **Case 4 (ON → OFF during pending flush):** Scheduled debounce timers cancelled and zero events emitted: **PASS**
- **Case 5 (OFF → ON):** Telemetry resumes normally: **PASS**
- **Case 6 (OFF → ON → OFF):** State transitions remain completely deterministic: **PASS**

---

## 16. Chrome Extension Context Lifecycle

Content scripts injected into webpages are inherently tied to the lifecycle of the host Chrome extension runtime. When an extension is reloaded or updated via `chrome://extensions` while an existing webpage (`http://localhost:3000/`) remains open, the content script running in that tab becomes orphaned:
- Its execution context is severed from the extension runtime, causing `chrome.runtime.id` to become `undefined`.
- Native Chromium bindings synchronously throw `Error: Extension context invalidated` whenever orphaned content scripts attempt to invoke extension APIs (such as `chrome.storage.local.get` or `chrome.runtime.sendMessage`).
- **Graceful Lifecycle Handling:** SentinelGuard implements proactive context guards (`isExtensionContextValid()`) and targeted exception handling (`isContextInvalidatedError()`). When an invalid context is detected, `content.js` gracefully tears down: it unregisters its DOM listener (`window.removeEventListener("mousemove", ...)`), clears in-memory buffers and timers, and terminates further communication without emitting uncaught runtime exceptions.
- **Recovery via Page Reload:** Reloading the webpage (`F5`) establishes a fresh content script context connected to the updated extension runtime, initializing a fresh session ID (`sess_<fresh-uuid>`) and resuming normal telemetry capture.
- **Independence from Protection Toggle:** This lifecycle behavior is a native property of Chrome extension architecture and is completely distinct from the user-facing Protection ON/OFF toggle state.

---

## 17. Known Limitations & Explicit Non-Goals

### Known Limitations:
- The 20 Hz sampling rate (~50 ms) is an engineering trade-off chosen for browser performance and battery conservation, not a certified ML-optimal sampling frequency.
- In-browser human mouse movements will rarely produce a mathematical 1.000 straightness due to optical mouse sensor noise and physiological hand tremors.
- Cursors moved outside the viewport or across iframes are bounded by standard browser event bubbling rules.

### Explicit Non-Goals (Strictly PLANNED for Later Phases):
- Keystroke dynamics and typing rhythm (Phase 5).
- Login form field detection and submit button tracking (Phase 5).
- Event batching across network requests (Phase 6).
- Django REST API backend endpoints (Phase 6).
- Machine learning model training, inference, and bot-risk scoring (Phase 6).
- Adaptive step-up OTP challenge logic (Phase 7).
- Centralized administrator monitoring dashboard (Phase 8).

---

## 18. Current Phase Status & Recommendation

- **Phase Status:** `IMPLEMENTED — PENDING MANUAL VERIFICATION`
- **Recommendation:** **`DO NOT COMMIT YET`** until Test 3 (clean OFF → ON toggle confirmation) and extension reload tests have been confirmed by the user.

---

## 19. Next Phase Boundary (Phase 5 Preview)

Once Phase 4 is marked complete:
- **Phase 5:** Focuses on **Typing Rhythm Telemetry & Login Interaction Detection**.
- Will capture keystroke timing biometrics (dwell time and flight time only; strictly zero character or key-identity logging) and login form focus/blur events. Zero backend, zero ML, zero OTP in Phase 5.
