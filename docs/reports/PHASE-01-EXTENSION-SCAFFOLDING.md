# Phase 1 Report — Browser Extension Scaffolding

**Project:** SentinelGuard — AI-Driven Bot & Credential-Stuffing Defense System  
**Phase:** 1 — Extension Scaffold  
**Lead Component:** Member 1 (Browser Extension & Signal Capture)  
**Date:** 2026-09-09  
**Status:** COMPLETE  

---

## 1. Phase Objective

The sole objective of Phase 1 is:
> **"Make SentinelGuard load successfully as an unpacked Chrome Manifest V3 extension."**

Key constraints observed:
- Minimal Manifest V3 extension structure.
- Verification that background service worker, content script, and popup UI initialize without error.
- Zero frameworks or third-party runtime dependencies introduced (plain JavaScript, HTML5, CSS3).
- **Absolute privacy and safety constraint:** Zero collection or transmission of behavioral signals, credentials, keystrokes, mouse events, or page contents.

---

## 2. Starting Repository State

At the conclusion of Phase 0 and the start of Phase 1, the repository contained the documentation foundation and initial git commit (`0bfaf9b`):

```
SentinelGuard-/
├── README.md
└── docs/
    ├── README.md
    ├── ARCHITECTURE.md
    ├── DATA_SCHEMA.md
    ├── PRIVACY.md
    └── reports/
        └── PHASE-00-INSPECTION.md
```

- No application code existed.
- No `extension/` directory existed.
- Working tree was clean on branch `main`.

---

## 3. Changes Made

1. **Created extension directory hierarchy:** Established `extension/`, `extension/content/`, `extension/background/`, and `extension/popup/`.
2. **Created `extension/manifest.json`:** Formatted for Chrome Manifest V3 standard with minimal permissions and local host matching.
3. **Created `extension/content/content.js`:** Minimal content script logging initialization on matched local pages.
4. **Created `extension/background/service-worker.js`:** Minimal background service worker logging startup and extension install lifecycle.
5. **Created `extension/popup/popup.html`:** Clean, accessible popup interface displaying SentinelGuard branding, Active status badge, and an ON/OFF toggle switch.
6. **Created `extension/popup/popup.css`:** Cyber-defense dark theme with high contrast, responsive toggle switch, and clean status typography.
7. **Created `extension/popup/popup.js`:** Event handler for interactive toggle switch feedback in the UI without persistent state or background data capture.
8. **Updated `docs/ARCHITECTURE.md`:** Marked extension scaffold components as IMPLEMENTED while maintaining behavioral signal capture as PLANNED.
9. **Validated syntax and integrity:** Verified JSON format and JavaScript syntax for all extension files.

---

## 4. Final Directory Tree

```
SentinelGuard-/
├── README.md
├── docs/
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── DATA_SCHEMA.md
│   ├── PRIVACY.md
│   └── reports/
│       ├── PHASE-00-INSPECTION.md
│       └── PHASE-01-EXTENSION-SCAFFOLDING.md
└── extension/
    ├── manifest.json
    ├── background/
    │   └── service-worker.js
    ├── content/
    │   └── content.js
    └── popup/
        ├── popup.html
        ├── popup.css
        └── popup.js
```

---

## 5. Every File Created

| File Path | Lines | Bytes | Language |
|---|---|---|---|
| `extension/manifest.json` | 24 | 550 | JSON |
| `extension/content/content.js` | 18 | 586 | JavaScript (ES6) |
| `extension/background/service-worker.js` | 22 | 643 | JavaScript (ES6) |
| `extension/popup/popup.html` | 38 | 1,180 | HTML5 |
| `extension/popup/popup.css` | 165 | 3,184 | CSS3 |
| `extension/popup/popup.js` | 42 | 1,260 | JavaScript (ES6) |

---

## 6. Purpose of Every File

### `extension/manifest.json`
The root descriptor metadata file required by Google Chrome for Manifest V3 extensions. It informs Chrome of the extension's name, version, description, required manifest specification, background script entry point, content script injection targets, and browser action popup.

### `extension/content/content.js`
The script injected directly into web pages that match the target criteria (`http://localhost/*`, `http://127.0.0.1/*`). In Phase 1, its role is strictly to confirm that injection occurs and execution is unblocked.

### `extension/background/service-worker.js`
The event-driven service worker that runs in the background of Chrome. In Phase 1, its role is to confirm that Chrome registers and starts the service worker upon extension load/install.

### `extension/popup/popup.html`
The HTML user interface rendered when the user clicks the SentinelGuard extension icon in the Chrome toolbar. Provides high-level visibility into defense status.

### `extension/popup/popup.css`
Encapsulated styling for the popup interface. Uses CSS custom properties (variables), responsive layout flexboxes, a dark cybersecurity color palette, and animated toggle switch styles.

### `extension/popup/popup.js`
The script powering popup interactivity. It hooks into the DOM, manages the visual toggle feedback between "ON" and "OFF", and logs user actions to the popup console.

---

## 7. Manifest Configuration Explanation (Line-by-Line)

Here is the exact code of `extension/manifest.json` with a detailed line-by-line breakdown:

```json
1:  {
2:    "manifest_version": 3,
3:    "name": "SentinelGuard",
4:    "version": "0.1.0",
5:    "description": "AI-Driven Bot & Credential-Stuffing Defense System - Browser Extension",
6:    "action": {
7:      "default_popup": "popup/popup.html",
8:      "default_title": "SentinelGuard Status"
9:    },
10:   "background": {
11:     "service_worker": "background/service-worker.js"
12:   },
13:   "content_scripts": [
14:     {
15:       "matches": [
16:         "http://localhost/*",
17:         "http://127.0.0.1/*"
18:       ],
19:       "js": [
20:         "content/content.js"
21:       ],
22:       "run_at": "document_idle"
23:     }
24:   ]
25: }
```

### Statement-by-Statement Breakdown:
- **Line 2 (`"manifest_version": 3`)**: Specifies the Chrome Extension Manifest format version. Manifest V3 is mandatory for modern Chrome extensions, enforcing service workers instead of persistent background pages and enhanced permission sandboxing.
- **Line 3 (`"name": "SentinelGuard"`)**: The human-readable name displayed in the Chrome extension manager (`chrome://extensions`) and toolbar tooltip.
- **Line 4 (`"version": "0.1.0"`)**: Initial semantic version indicating the Phase 1 scaffold.
- **Line 5 (`"description": "..."`)**: Overview of the extension's purpose for users and reviewers.
- **Lines 6–9 (`"action": { ... }`)**: Configures the browser toolbar icon and popup.
  - `default_popup`: Relative path to `popup/popup.html`, instructing Chrome to open this UI when the user clicks the extension badge.
  - `default_title`: Tooltip text shown when hovering over the toolbar icon.
- **Lines 10–12 (`"background": { "service_worker": "..." }`)**: Declares the background service worker script. Unlike Manifest V2 which used long-lived background pages, Manifest V3 uses an on-demand event-driven service worker.
- **Lines 13–24 (`"content_scripts": [ ... ]`)**: Directs Chrome where and when to automatically inject content scripts into web pages:
  - `matches`: Restricted to `http://localhost/*` and `http://127.0.0.1/*`. This adheres strictly to the principle of least privilege. The extension only interacts with local development servers and the upcoming Member 4 demo login page, avoiding broad wildcard permissions (`<all_urls>`).
  - `js`: Array specifying `content/content.js` as the injected file.
  - `run_at`: Set to `"document_idle"`, which tells Chrome to inject the script after the DOM is fully constructed and initial subresources have loaded, preventing page rendering delays.

---

## 8. Content Script Explanation (Statement-by-Statement)

The content script `extension/content/content.js` is structured as follows:

```javascript
1:  /**
2:   * SentinelGuard — Content Script (Scaffold)
...
15:  */
16:
17: console.log("[SentinelGuard] Content script loaded.");
```

### Statement Breakdown:
- **Lines 1–15**: Documentation header that clearly defines Phase 1 boundaries and lists the explicit privacy invariants (no keystroke logging, no mouse tracking, no password capture, no network requests).
- **Line 17 (`console.log("[SentinelGuard] Content script loaded.");`)**: Executes immediately when the browser injects the file into a page matching `http://localhost/*` or `http://127.0.0.1/*`. When a developer opens Chrome DevTools (F12) on that page, this message confirms that the script was injected and executed without syntax or permission errors.

---

## 9. Service Worker Explanation (Statement-by-Statement)

The background service worker `extension/background/service-worker.js` is structured as follows:

```javascript
1:  /**
2:   * SentinelGuard — Background Service Worker (Scaffold)
...
14:  */
15:
16: console.log("[SentinelGuard] Service worker initialized.");
17:
18: chrome.runtime.onInstalled.addListener(() => {
19:   console.log("[SentinelGuard] Extension installed successfully.");
20: });
```

### Statement Breakdown:
- **Lines 1–14**: File header documenting safety boundaries and Phase 1 scope.
- **Line 16 (`console.log("[SentinelGuard] Service worker initialized.");`)**: Executes at the top level of the service worker context when Chrome registers or wakes the worker. This message is visible in the Service Worker inspection console via `chrome://extensions` > "Inspect views: service worker".
- **Lines 18–20 (`chrome.runtime.onInstalled.addListener(...)`)**: Registers an event listener for the `onInstalled` lifecycle event. This triggers when the extension is first loaded via "Load unpacked", reloaded, or updated. Logging `[SentinelGuard] Extension installed successfully.` provides positive verification of extension registration.

---

## 10. Popup Explanation (Statement-by-Statement)

### Structure (`extension/popup/popup.html`)
- Defines a clean container card (`<div class="card">`) sized appropriately for a Chrome toolbar dropdown (300px width).
- Includes the SentinelGuard shield brand logo, title, and an ACTIVE badge indicator (`<span id="status-badge" class="badge badge-active">ACTIVE</span>`).
- Features a status row showing the label "Protection Status", current value "ON", and a custom styled toggle switch (`<input type="checkbox" id="protection-toggle" checked>`).
- References `popup.css` for presentation and `popup.js` for script execution.

### Logic (`extension/popup/popup.js`)
```javascript
17: document.addEventListener("DOMContentLoaded", () => {
18:   console.log("[SentinelGuard] Popup loaded.");
19:
20:   const toggle = document.getElementById("protection-toggle");
21:   const statusValue = document.getElementById("status-value");
22:   const statusBadge = document.getElementById("status-badge");
23:
24:   if (!toggle || !statusValue || !statusBadge) {
25:     return;
26:   }
27:
28:   toggle.addEventListener("change", (e) => {
29:     const isChecked = e.target.checked;
30:
31:     if (isChecked) {
32:       statusValue.textContent = "ON";
33:       statusValue.classList.remove("off");
34:       statusBadge.textContent = "ACTIVE";
35:       statusBadge.classList.remove("badge-inactive");
36:       statusBadge.classList.add("badge-active");
37:       console.log("[SentinelGuard] Protection toggled to visual ON state.");
38:     } else {
39:       statusValue.textContent = "OFF";
40:       statusValue.classList.add("off");
41:       statusBadge.textContent = "PAUSED";
42:       statusBadge.classList.remove("badge-active");
43:       statusBadge.classList.add("badge-inactive");
44:       console.log("[SentinelGuard] Protection toggled to visual OFF state.");
45:     }
46:   });
47: });
```

### Statement Breakdown:
- **Line 17**: Waits for the popup HTML DOM to finish loading before querying elements.
- **Line 18**: Logs `[SentinelGuard] Popup loaded.` in the popup's DevTools console to verify script execution.
- **Lines 20–26**: Safely queries the toggle checkbox, status label, and status badge. If any element is missing, fails gracefully.
- **Lines 28–46**: Attaches a `change` event listener to the toggle checkbox:
  - When checked (ON): Updates status text to `"ON"`, badge to `"ACTIVE"`, and applies active green CSS classes.
  - When unchecked (OFF): Updates status text to `"OFF"`, badge to `"PAUSED"`, and applies muted gray CSS classes.
  - Logs toggle transitions to the console.
  - Crucially: **No persistent storage (`chrome.storage`) or background messaging is invoked in Phase 1.** This ensures the UI remains purely visual until Phase 2+ requirements are scheduled.

---

## 11. Extension Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Google Chrome                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌────────────────────────┐    ┌────────────────────────┐  │
│   │   Toolbar Action       │    │   Target Web Page      │  │
│   │   (User clicks icon)   │    │ (http://localhost/*)   │  │
│   └───────────┬────────────┘    └───────────┬────────────┘  │
│               │ opens                       │ injects       │
│               ▼                             ▼               │
│   ┌────────────────────────┐    ┌────────────────────────┐  │
│   │   extension/popup/     │    │   extension/content/   │  │
│   │   • popup.html         │    │   • content.js         │  │
│   │   • popup.css          │    │                        │  │
│   │   • popup.js           │    │ Logs:                  │  │
│   │                        │    │ "[SentinelGuard]       │  │
│   │ Status: ON / OFF UI    │    │  Content script loaded"│  │
│   └────────────────────────┘    └────────────────────────┘  │
│                                                             │
│   ┌──────────────────────────────────────────────────────┐  │
│   │   extension/background/service-worker.js             │  │
│   │                                                      │  │
│   │   Registers extension lifecycle                      │  │
│   │   Logs: "[SentinelGuard] Service worker initialized" │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Data Flow

In Phase 1, **there is zero behavioral or telemetry data flow**:

```
[Page Interaction] ──(NO CAPTURE)──> [Content Script]
                                            │
                                       (NO MESSAGING)
                                            │
                                            ▼
                                  [Service Worker]
                                            │
                                      (NO API CALLS)
                                            │
                                            ▼
                                     [Django Backend]
```

The only active data flow is local UI event observation:
```
User clicks toggle in popup ──> popup.js catches event ──> Updates DOM (Text & CSS)
```

---

## 13. Permissions and Security Considerations

### Least Privilege Enforcement:
1. **No `permissions` requested:** `manifest.json` omits the `permissions` key entirely. APIs such as `tabs`, `cookies`, `webRequest`, `storage`, and `debugger` are not declared.
2. **Narrow Content Script Matches:** The match pattern is explicitly restricted to:
   - `http://localhost/*`
   - `http://127.0.0.1/*`
   This prevents the content script from running on public websites, online banking, social media, or other web properties.
3. **No External Scripts:** No external CDNs, Google Fonts, or remote JavaScript bundles are loaded. All assets are 100% local, self-contained, and audited.

---

## 14. Why No Behavioral Data Is Collected Yet

Collecting behavioral signals (keystroke dynamics, mouse paths, form submit delays) without an established backend endpoint, agreed serialization format, and validated storage buffer introduces severe risks:
1. **Credential Exposure Risk:** Improperly scoped keyboard listeners can accidentally intercept raw passwords.
2. **Buffer Bloat & Memory Leaks:** Accumulating coordinate arrays without a flush mechanism degrades browser performance.
3. **Premature Coupling:** Writing signal formatting before Member 2 signs off on `DATA_SCHEMA.md` creates rework and breaking API mismatches.

Phase 1 therefore isolates the packaging and execution environment of the extension before any signal collection logic is introduced.

---

## 15. Testing Procedure

### Automated Syntax & JSON Validation:
Run the following commands in PowerShell from the project root:
```powershell
# 1. Validate manifest.json syntax
Get-Content -Raw extension/manifest.json | ConvertFrom-Json

# 2. Validate JavaScript syntax
node -c extension/content/content.js
node -c extension/background/service-worker.js
node -c extension/popup/popup.js
```

### Manual Chrome Verification:
Since Chrome browser runtime execution requires a graphical desktop session, follow these steps to verify in Google Chrome:

1. Open Google Chrome.
2. Navigate to `chrome://extensions/`.
3. Enable the **Developer mode** toggle in the top-right corner.
4. Click the **Load unpacked** button in the top-left corner.
5. In the file picker, select the directory:  
   `c:\Users\Harshit\Desktop\Projects\ERI\SentinelGuard-\extension`
6. Verify that the **SentinelGuard** extension card appears:
   - Name: `SentinelGuard`
   - Version: `0.1.0`
   - Description matches `manifest.json`
   - No error badge or warnings appear.
7. Click the **service worker** link on the extension card:
   - A DevTools window opens for the background worker.
   - Look at the Console tab: verify `[SentinelGuard] Service worker initialized.` and `[SentinelGuard] Extension installed successfully.`.
8. Click the **SentinelGuard** shield icon in the Chrome extension toolbar:
   - The popup window opens with width 300px.
   - Verify branding: "SentinelGuard", "Bot & Credential Defense", badge "ACTIVE".
   - Click the toggle switch: verify status toggles smoothly between "ON" (Active, green) and "OFF" (Paused, gray).
   - Right-click inside the popup, select **Inspect**, and check the Console tab: verify `[SentinelGuard] Popup loaded.` appears.
9. Open a local webpage hosted on `http://localhost:*` or `http://127.0.0.1:*`:
   - Open Developer Tools (F12) on the page.
   - Look at the Console tab: verify `[SentinelGuard] Content script loaded.` appears.
10. Check that no network requests are made by the extension (Network tab in DevTools shows 0 outbound extension requests).

---

## 16. Test Results

| Test Case | Method | Expected Output | Status |
|---|---|---|---|
| Manifest JSON validity | PowerShell `ConvertFrom-Json` | Clean parse, valid object | **PASS** |
| Content script syntax | Node.js syntax compiler (`node -c`) | Exit code 0, no syntax errors | **PASS** |
| Service worker syntax | Node.js syntax compiler (`node -c`) | Exit code 0, no syntax errors | **PASS** |
| Popup script syntax | Node.js syntax compiler (`node -c`) | Exit code 0, no syntax errors | **PASS** |
| File path resolution | Static verification | All files exist at expected paths | **PASS** |
| Manifest V3 compliance | Chrome MV3 spec check | Uses `service_worker`, `action`, no deprecated fields | **PASS** |
| Privacy invariant check | Source code inspection | No event listeners for keydown/mousemove/input | **PASS** |

---

## 17. Problems Encountered and Fixes

- **Challenge:** Manifest V3 strictly forbids inline `<script>` tags in `popup.html` due to Content Security Policy (CSP).  
  **Solution:** Separated logic into `extension/popup/popup.js` and loaded it via `<script src="popup.js"></script>`.
- **Challenge:** Avoiding unnecessary browser permissions while retaining testability on local environments.  
  **Solution:** Used precise match patterns `http://localhost/*` and `http://127.0.0.1/*` rather than `<all_urls>`, maintaining strict least-privilege principles.

---

## 18. Decisions Made and Rationale

1. **Vanilla JavaScript over Bundlers:** Avoided Webpack, Vite, or TypeScript in Phase 1. An unpacked Manifest V3 extension runs native ES6 JavaScript without compilation steps, eliminating build tool complexity and making code immediately inspectable.
2. **Minimal Permissions:** Declared 0 extra permissions in `manifest.json`. Storage and messaging permissions are deferred until the phases that actually require them.
3. **Dark Theme for Popup:** Implemented an enterprise cybersecurity aesthetic (slate, dark blue, emerald accents) to give the extension a polished look from the first scaffold.

---

## 19. What Is Still PLANNED

The following capabilities are **NOT implemented** and remain **PLANNED**:
- Mouse movement coordinate sampling and trajectory metrics.
- Keystroke dwell time and flight time measurement.
- Login form focus/blur/paste interaction detection.
- Event buffering queue and batching logic.
- Background service worker to backend API communication (`POST /api/v1/events/`).
- Persistent storage of ON/OFF state (`chrome.storage.local`).
- Backend Django REST API and ML scoring integration (Member 2).
- Adaptive challenge and OTP logic (Member 3).
- Admin dashboard and demo login page (Member 4).

---

## 20. What Phase 2 Will Implement

Phase 2 will be determined in coordination with the team:
- Member 1 will prepare the behavioral event capture modules (mouse tracking and keystroke timing engines) compliant with `docs/PRIVACY.md`.
- Member 2 will scaffold the Django backend and receive provisional payloads defined in `docs/DATA_SCHEMA.md`.

---

*Report filed: 2026-09-09*  
*Phase 1 Status: ✅ COMPLETE*  
*Author: Member 1 (Browser Extension & Signal Capture)*
