# Phase 2 Report — Content-Script to Service-Worker Runtime Messaging

**Project:** SentinelGuard — AI-Driven Bot & Credential-Stuffing Defense System  
**Phase:** 2 — Internal Extension Messaging Pipeline  
**Lead Component:** Member 1 (Browser Extension & Signal Capture)  
**Date:** 2026-09-10  
**Status:** PHASE 2 COMPLETE — MANUALLY VERIFIED  

---

## 1. Phase Objective

The sole objective of Phase 2 is:
> **"Establish and verify one-way communication from `content.js` to `service-worker.js` using Chrome Manifest V3 Runtime Messaging."**

This phase proves that the content script, running in an isolated webpage context, can transmit a minimal, safe development test event (`TEST_EVENT`) to the background service worker, and that the service worker can reliably receive, validate, and log the event.

**Critical Scope Constraint:**  
This phase does **NOT** implement behavioral signal capture, mouse tracking, keystroke tracking, event batching, or backend API communication.

---

## 2. Starting State

At the conclusion of Phase 1 and the start of Phase 2:
- Commit `3111076` marked Phase 1 complete on branch `main`.
- The Chrome Manifest V3 extension scaffold was fully functional:
  - `extension/manifest.json`: Validated MV3 descriptor.
  - `extension/background/service-worker.js`: Initialized lifecycle; logged startup.
  - `extension/content/content.js`: Injected into `http://localhost/*`; logged load.
  - `extension/popup/`: Rendered UI with interactive toggle.
  - `test-page/index.html`: Static test harness served on `http://localhost:3000/`.
- **Zero communication** existed between `content.js` and `service-worker.js`.

---

## 3. Why Content-Script / Service-Worker Messaging Is Needed

Under Google Chrome's Manifest V3 security architecture, extensions operate under strict process and context isolation:
1. **Isolated Worlds:** Content scripts run in the context of the web page but in an "isolated world". While they have access to the page DOM, they operate in an isolated JavaScript execution context.
2. **Security & Architectural Separation:** In modern Manifest V3 design, background tasks, network requests to backend APIs, and centralized state management belong exclusively in the background service worker, not directly inside individual content scripts on every tab.
3. **Future Signal Pipeline:** In future phases, when Member 1 introduces behavioral signal capture (mouse dynamics and keystroke timing), those events must be relayed from the content script on the login page to the background service worker for buffering, batching, and secure dispatch to Member 2's Django REST API.
4. **Validation of the Pipeline:** Establishing and validating the messaging pipeline with a completely benign dummy event in Phase 2 ensures that the IPC (Inter-Process Communication) mechanism functions before any real data or buffering logic is introduced.

---

## 4. Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                             Google Chrome                              │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ Web Page Target: http://localhost:3000/                        │   │
│   │ (test-page/index.html)                                         │   │
│   │                                                                │   │
│   │   ┌────────────────────────────────────────────────────────┐   │   │
│   │   │ extension/content/content.js                           │   │   │
│   │   │                                                        │   │   │
│   │   │ 1. Logs: "[SentinelGuard] Content script loaded."       │   │   │
│   │   │ 2. Dispatches safe payload via:                        │   │   │
│   │   │    chrome.runtime.sendMessage({ type: "TEST_EVENT" })  │   │   │
│   │   │ 3. Logs: "[SentinelGuard] Test event sent."            │   │   │
│   │   └───────────────────────────┬────────────────────────────┘   │   │
│   └───────────────────────────────┼────────────────────────────────┘   │
│                                   │                                    │
│                                   │ Chrome MV3 Runtime Message Bus     │
│                                   │ (Internal IPC)                     │
│                                   ▼                                    │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ Background Context: extension/background/service-worker.js     │   │
│   │                                                                │   │
│   │   chrome.runtime.onMessage.addListener(...)                    │   │
│   │                                                                │   │
│   │   1. Receives message payload                                  │   │
│   │   2. Validates: message.type === "TEST_EVENT"                  │   │
│   │   3. Logs: "[SentinelGuard] Test event received."              │   │
│   │   4. Logs: "[SentinelGuard] Test event timestamp: <timestamp>" │   │
│   │   5. Returns acknowledgment: { status: "ACK" }                 │   │
│   │   6. (NO storage, NO network request, NO ML processing)        │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Files Modified

| File Path | Nature of Change | Lines Added / Modified |
|---|---|---|
| `extension/content/content.js` | Added `chrome.runtime.sendMessage` dispatch | 16 lines added |
| `extension/background/service-worker.js` | Added `chrome.runtime.onMessage` listener | 12 lines added |
| `docs/ARCHITECTURE.md` | Updated status to `IMPLEMENTED — PHASE 2` | Documented status |

**Files Explicitly Preserved Without Modification:**
- `extension/manifest.json` (No permission changes required; runtime messaging is built into MV3 core)
- `extension/popup/*` (`popup.html`, `popup.css`, `popup.js`)
- `test-page/index.html`
- Root `README.md` (Deferred until manual verification)

---

## 6. Exact Implementation Changes

### 6.1. Content Script (`extension/content/content.js`)

#### Before:
```javascript
console.log("[SentinelGuard] Content script loaded.");
```

#### After:
```javascript
console.log("[SentinelGuard] Content script loaded.");

// Phase 2: Send a minimal, safe test event to service worker
const testPayload = {
  type: "TEST_EVENT",
  timestamp: Date.now()
};

chrome.runtime.sendMessage(testPayload, () => {
  if (chrome.runtime.lastError) {
    // Suppress or handle if background worker is spinning up
  }
});

console.log("[SentinelGuard] Test event sent.");
```

---

### 6.2. Background Service Worker (`extension/background/service-worker.js`)

#### Before:
```javascript
console.log("[SentinelGuard] Service worker initialized.");

chrome.runtime.onInstalled.addListener(() => {
  console.log("[SentinelGuard] Extension installed successfully.");
});
```

#### After:
```javascript
console.log("[SentinelGuard] Service worker initialized.");

chrome.runtime.onInstalled.addListener(() => {
  console.log("[SentinelGuard] Extension installed successfully.");
});

// Phase 2: Listen for test message from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === "TEST_EVENT") {
    console.log("[SentinelGuard] Test event received.");
    console.log("[SentinelGuard] Test event timestamp:", message.timestamp);
    if (sendResponse) {
      sendResponse({ status: "ACK" });
    }
  }
});
```

---

## 7. Detailed Explanation of Important Code Lines

### In `extension/content/content.js`:
- **`const testPayload = { type: "TEST_EVENT", timestamp: Date.now() };`**: Constructs an immutable, safe JavaScript object containing only an event discriminator (`"TEST_EVENT"`) and an epoch millisecond timestamp (`Date.now()`). No page content, credentials, or user inputs are referenced.
- **`chrome.runtime.sendMessage(testPayload, () => { ... });`**: Invokes the Manifest V3 messaging API. This serializes the payload using the structured clone algorithm and routes it asynchronously to the extension's background service worker.
- **`if (chrome.runtime.lastError)`**: Defensive error handler callback. Inspecting `chrome.runtime.lastError` prevents Chrome from logging an unchecked runtime warning if the background service worker is waking up or temporarily inactive.
- **`console.log("[SentinelGuard] Test event sent.");`**: Confirms in the webpage DevTools console that the test message has been submitted to the browser's runtime dispatch queue.

### In `extension/background/service-worker.js`:
- **`chrome.runtime.onMessage.addListener((message, sender, sendResponse) => { ... });`**: Registers a persistent message listener in the background service worker context. When Chrome wakes the service worker upon message arrival, this listener handles the payload.
- **`if (message && message.type === "TEST_EVENT")`**: Strict type discrimination. Ensures that malformed, null, or unknown messages are ignored safely without raising runtime exceptions.
- **`console.log("[SentinelGuard] Test event received.");`**: Outputs a clear, unambiguous log line in the service worker DevTools console confirming message delivery.
- **`console.log("[SentinelGuard] Test event timestamp:", message.timestamp);`**: Outputs the payload's timestamp, confirming that payload data arrived intact without corruption.
- **`sendResponse({ status: "ACK" });`**: Sends a clean acknowledgment back to the sender, concluding the message transaction.

---

## 8. Message Schema

The Phase 2 message schema is intentionally minimal and strictly defined:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SentinelGuardPhase2TestMessage",
  "type": "object",
  "properties": {
    "type": {
      "type": "string",
      "enum": ["TEST_EVENT"]
    },
    "timestamp": {
      "type": "integer",
      "description": "Milliseconds since Unix epoch (Date.now())"
    }
  },
  "required": ["type", "timestamp"],
  "additionalProperties": false
}
```

### Example Payload:
```json
{
  "type": "TEST_EVENT",
  "timestamp": 1773123600000
}
```

---

## 9. Data Flow

```
1. Browser loads http://localhost:3000/
2. Chrome injects extension/content/content.js at document_idle
3. content.js executes:
   a. console.log("[SentinelGuard] Content script loaded.")
   b. Creates testPayload: { type: "TEST_EVENT", timestamp: 1773123600000 }
   c. Invokes chrome.runtime.sendMessage(testPayload)
   d. console.log("[SentinelGuard] Test event sent.")
4. Chrome runtime clones payload and wakes background service worker
5. service-worker.js executes onMessage listener:
   a. Evaluates message.type === "TEST_EVENT" (true)
   b. console.log("[SentinelGuard] Test event received.")
   c. console.log("[SentinelGuard] Test event timestamp: 1773123600000")
   d. Calls sendResponse({ status: "ACK" })
```

---

## 10. Chrome Runtime Messaging Explanation

- **Mechanism:** Chrome extensions communicate across contexts using the `chrome.runtime` API. Messages are passed through an internal Chromium message bus that does not touch the network layer.
- **Permission Requirements:** Built-in to Chrome Extensions. No declaration under `"permissions"` in `manifest.json` is needed for basic extension-internal messaging.
- **Manifest V3 Lifecycle Handling:** In Manifest V3, background service workers are ephemeral and terminate when idle. Chrome automatically wakes the service worker when `chrome.runtime.sendMessage` is dispatched, ensuring reliable delivery even when the worker was suspended.

---

## 11. Service-Worker Message Handling Explanation

- **Listener Registration:** `chrome.runtime.onMessage.addListener` must be registered synchronously at the top level of the service worker script so Chrome can register the event before executing asynchronous tasks.
- **Validation:** Incoming objects are validated before property access to prevent prototype pollution or TypeError exceptions.
- **Zero Side Effects:** In Phase 2, the message handler strictly logs the received timestamp. It does not write to `chrome.storage`, make `fetch()` calls, or invoke cryptographic functions.

---

## 12. Privacy and Security Considerations

1. **Zero External Surface:** Runtime messaging is strictly internal to the SentinelGuard extension. No web pages or external extensions can intercept these messages.
2. **Origin Restriction:** Content scripts only run on origins matched in `manifest.json` (`http://localhost/*`, `http://127.0.0.1/*`).
3. **No PII or Sensitive Data:** The message contains only an epoch timestamp and a hardcoded string.

---

## 13. What Data Is Deliberately NOT Collected

| Category | Deliberately Excluded Items | Status |
|---|---|---|
| **Credentials** | Passwords, usernames, email addresses, PINs | **NOT IMPLEMENTED / NEVER COLLECTED** |
| **Form Inputs** | Form field values, text contents, clipboard data | **NOT IMPLEMENTED / NEVER COLLECTED** |
| **Mouse Telemetry** | Coordinates `(x, y)`, velocity, acceleration, trajectories | **PLANNED (Future Phase)** |
| **Keyboard Telemetry** | Key codes, dwell times, flight times, typing rhythm | **PLANNED (Future Phase)** |
| **Form Interaction** | Focus/blur events, field dwell times, submit delays | **PLANNED (Future Phase)** |
| **Network & Backend** | HTTP POST requests, `/api/v1/events/`, Django calls | **PLANNED (Future Phase)** |
| **Analytics & ML** | Risk scores, feature vectors, inference calls | **PLANNED (Future Phase)** |
| **Persistence** | Cookies, local storage, indexedDB, service worker cache | **PLANNED (Future Phase)** |

---

## 14. Testing Procedure

### Static Validation:
Run JavaScript syntax compilation on both modified files:
```powershell
node -c extension/content/content.js
node -c extension/background/service-worker.js
```

### Listener Audit:
Verify that no forbidden listeners exist in the extension code:
```powershell
Select-String -Path "extension\content\content.js" -Pattern "(mousemove|keydown|keyup|input|submit)"
```

---

## 15. Automated / Static Validation Results

| Test Case | Command / Tool | Expected Output | Actual Result | Status |
|---|---|---|---|---|
| Content script syntax | `node -c extension/content/content.js` | Exit code 0 | Clean exit (0 errors) | **PASS** |
| Service worker syntax | `node -c extension/background/service-worker.js` | Exit code 0 | Clean exit (0 errors) | **PASS** |
| Forbidden listener audit | PowerShell pattern matching | 0 matches | 0 matches | **PASS** |
| Permission check | `manifest.json` inspection | No extra permissions | 0 permissions declared | **PASS** |
| Chrome Runtime Messaging | Manual Chrome DevTools test | Logs on both sides; timestamp transferred | Verified: 1789020905477 | **PASS — MANUALLY VERIFIED** |

---

## 16. Manual Chrome Verification Procedure

To manually verify the runtime messaging pipeline in Google Chrome:

### Prerequisites:
1. Ensure the local test server is running:
   ```powershell
   python -m http.server 3000 --directory test-page
   ```
   *(Confirm accessible at `http://localhost:3000/`)*

### Steps:
1. **Reload Extension:**
   - Navigate to `chrome://extensions/`.
   - Locate the **SentinelGuard** card.
   - Click the circular **Reload** icon on the card to pick up code changes.
2. **Open Service Worker DevTools:**
   - Click the **service worker** link on the SentinelGuard card.
   - A dedicated Chrome DevTools window opens for the background worker.
   - Switch to the **Console** tab.
3. **Open the Test Page:**
   - In a Chrome tab, navigate to `http://localhost:3000/`.
4. **Open Webpage DevTools:**
   - Press `F12` (or right-click → **Inspect**) on the test page.
   - Switch to the **Console** tab.
5. **Observe Webpage Console Output:**
   - Verify that the following logs appear in order:
     ```
     [SentinelGuard] Content script loaded.
     [SentinelGuard] Test event sent.
     ```
6. **Observe Service Worker Console Output:**
   - Switch back to the Service Worker DevTools Console window.
   - Verify that the following logs appear:
     ```
     [SentinelGuard] Test event received.
     [SentinelGuard] Test event timestamp: <numeric_timestamp>
     ```
7. **Verify Network Isolation:**
   - Inspect the Network tab in both DevTools windows.
   - Confirm that zero network requests are made to any remote or backend endpoints.

### 16.1. Actual Manual Verification Evidence (Google Chrome)

Manual verification was performed in Google Chrome with the unpacked SentinelGuard extension loaded and the local test harness (`python -m http.server 3000 --directory test-page`) serving `http://localhost:3000/`.

#### Webpage DevTools Console (`http://localhost:3000/`):
```
[SentinelGuard] Content script loaded.
[SentinelGuard] Test event sent.
```

#### Service Worker DevTools Console:
```
[SentinelGuard] Service worker initialized.
[SentinelGuard] Test event received.
[SentinelGuard] Test event timestamp: 1789020905477
```

#### Verification Analysis:
1. **End-to-End Pipeline Proven:**
   ```
   localhost webpage
          ↓
   content.js
          ↓
   chrome.runtime.sendMessage()
          ↓
   service-worker.js
          ↓
   chrome.runtime.onMessage
          ↓
   TEST_EVENT received
   ```
2. **Payload & Timestamp Integrity:** The epoch millisecond timestamp (`1789020905477`) was transferred without distortion or serialization errors from the webpage's content script to the background service worker context.
3. **Absence of Behavioral Telemetry:** As designed, zero mouse movement listeners, mouse coordinates, keyboard capture, typing rhythm timing, login detection, event buffering, or backend API transmissions exist. All behavioral signal capture remains explicitly **PLANNED / NOT IMPLEMENTED**.

---

## 17. Problems Encountered

- **Timing & Unchecked Runtime Errors:** In Chrome MV3, if a content script calls `chrome.runtime.sendMessage` while the service worker is transitioning or if no response callback inspects `chrome.runtime.lastError`, Chrome may print `Unchecked runtime.lastError: Could not establish connection`.
- **Solution Applied:** Added a defensive callback to `chrome.runtime.sendMessage` that accesses `chrome.runtime.lastError`, preventing false-positive warnings in the developer console.

---

## 18. Fixes Applied

- Implemented defensive callback handling in `extension/content/content.js`.
- Implemented payload validation guard (`if (message && message.type === "TEST_EVENT")`) in `extension/background/service-worker.js`.
- Added response callback acknowledgment (`sendResponse({ status: "ACK" })`) to cleanly conclude the IPC transaction.

---

## 19. Final Repository Tree

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
│       ├── PHASE-01-EXTENSION-SCAFFOLDING.md
│       └── PHASE-02-MESSAGING.md
├── extension/
│   ├── manifest.json
│   ├── background/
│   │   └── service-worker.js
│   ├── content/
│   │   └── content.js
│   └── popup/
│       ├── popup.html
│       ├── popup.css
│       └── popup.js
└── test-page/
    └── index.html
```

---

## 20. Phase 2 Limitations

- **Single Test Event Only:** Sends exactly one dummy test event upon script load.
- **No Event Queue:** Does not queue, buffer, or persist events.
- **No Real Telemetry:** Does not capture real user behavioral signals.
- **No Backend Connection:** Does not transmit data outside the browser extension process.

---

## 21. What Phase 3 Will Implement

Phase 3 will build upon the verified messaging pipeline established in Phase 2:
- **Member 1:** Introduce behavioral event listeners (mouse movement coordinates, keystroke timing intervals) adhering strictly to `docs/PRIVACY.md` (no key values, no password fields).
- **Member 1:** Implement an in-memory event buffer (`extension/utils/signal_buffer.js`) to batch events before passing them to the service worker.
- **Member 2:** Stand up the initial Django REST API endpoint (`POST /api/v1/events/`) according to `docs/DATA_SCHEMA.md`.

---

*Report updated: 2026-09-10*  
*Phase 2 Status: ✅ COMPLETE — MANUALLY VERIFIED*  
*Author: Member 1 (Browser Extension & Signal Capture)*
