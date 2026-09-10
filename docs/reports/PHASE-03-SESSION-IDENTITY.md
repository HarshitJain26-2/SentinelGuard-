# Phase 3 Report — Session and Event Identity Foundation

**Project:** SentinelGuard — AI-Driven Bot & Credential-Stuffing Defense System  
**Phase:** 3 — Session & Event Identity Foundation  
**Lead Component:** Member 1 (Browser Extension & Signal Capture)  
**Date:** 2026-09-10  
**Status:** PHASE 3 COMPLETE — MANUALLY VERIFIED  

---

## 1. Phase Objective

The sole objective of Phase 3 is:
> **"Establish the architectural foundation for Session Identity, Event Identity, and Structured Event Envelopes in SentinelGuard without collecting actual behavioral telemetry."**

This phase defines:
1. **Session Identity:** How a logical login interaction attempt is uniquely identified and bounded in time.
2. **Event Identity:** How individual events in the future telemetry stream are uniquely identified.
3. **Event Envelope:** The standardized, validated metadata container used for all internal and external event passing.
4. **Validation Logic:** Strict runtime validation on the receiving end (background service worker) to enforce structural correctness and reject malformed envelopes.

**Critical Scope Invariant:**  
This phase implements **ONLY** identity and metadata structures. It does **NOT** capture mouse coordinates, keyboard content, typing rhythm, form values, credentials, or DOM data.

---

## 2. Starting Architecture

At the conclusion of Phase 2 (commit `1e817bb`):
- Content script injects into target local pages (`http://localhost/*`).
- One-way runtime messaging (`chrome.runtime.sendMessage` → `chrome.runtime.onMessage`) was verified with a minimal test message `{ type: "TEST_EVENT", timestamp: ... }`.
- Service worker logs incoming messages.
- **Limitation at start of Phase 3:** Messages had no session grouping, no unique event identifiers, no schema validation, and no structured envelope.

---

## 3. Problem Being Solved

In an AI-driven bot defense system:
1. **Disjointed Events:** Without an event identifier, downstream systems (feature engineering pipelines, ML scoring models, step-up challenge triggers) cannot deduplicate, correlate, or audit individual actions.
2. **Session Collision & Interleaving:** A user may open multiple tabs, reload a page, or attempt multiple logins. Without a clean session identity abstraction, telemetry from different tabs or attempts could interleave, polluting feature calculations (e.g., combining keystrokes from Tab A with mouse movement from Tab B).
3. **Privacy Risk of Ad-Hoc IDs:** If session tracking relies on cookies, IP addresses, browser fingerprinting, or user account names, it violates user privacy. SentinelGuard requires cryptographically opaque, non-meaningful session identifiers.

---

## 4. Why Event Identity Is Necessary

Every telemetry event emitted by SentinelGuard must have an immutable, unique identifier (`event_id`):
- **Deduplication:** Prevents duplicate event processing if network retries occur in later phases.
- **Auditability & Traceability:** Allows the backend and admin dashboard to trace high-risk events back to the specific interaction instance.
- **Time-Series Ordering:** Guarantees unambiguous identity when multiple events share identical millisecond timestamps.

---

## 5. Why Session Identity Is Necessary

A logical "session" represents a discrete login interaction episode:
- **Feature Computation Window:** Keystroke dynamics (dwell time, flight time) and mouse dynamics (velocity, curvature) are aggregated across the duration of a single login attempt.
- **Tab Isolation:** Actions occurring in Tab A must never contaminate the feature vector computed for Tab B.
- **Lifecycle Bounding:** A session begins when the login page is loaded and terminates when the page is unloaded, navigated, or submitted.

---

## 6. Session Lifecycle Definition

| Lifecycle Event | Behavior & Handling |
|---|---|
| **Creation** | Created immediately when `content.js` executes upon page load (`document_idle`). |
| **Location** | Held in private, in-memory scope within the content script's isolated world (`currentSessionId`). |
| **Persistence** | In-memory only. Zero persistence in `localStorage`, cookies, or `chrome.storage`. |
| **Reuse** | Reused for every telemetry event generated during that specific page observation lifecycle. |
| **Page Reload** | Page reload terminates the previous JavaScript context. A completely fresh, unlinked session ID is generated on reload. |
| **Multiple Tabs** | Each browser tab instantiates its own isolated content script instance with its own independent session ID. No cross-tab session leakage. |
| **Expiration** | Naturally destroyed by the browser garbage collector when the tab is closed or navigated away. |

---

## 7. Event Lifecycle Definition

```
[Interaction / Trigger] 
       │
       ▼
1. SentinelIdentity.createEventEnvelope()
   - Generates unique event_id (evt_<uuid-v4>)
   - Attaches current session_id (sess_<uuid-v4>)
   - Records epoch millisecond timestamp (Date.now())
   - Encloses payload data (empty {} in Phase 3)
       │
       ▼
2. Dispatched via chrome.runtime.sendMessage()
       │
       ▼
3. Received by service-worker.js via chrome.runtime.onMessage
       │
       ▼
4. SentinelIdentity.validateEventEnvelope()
   - Validates event_type string
   - Validates event_id format
   - Validates session_id format
   - Validates timestamp range
       │
       ▼
5. Validation Passed: Log metadata / (Future: Buffer & Batch)
   Validation Failed: Log rejection warning & sendResponse({ status: "REJECTED" })
```

---

## 8. Session ID Generation

- **Algorithm:** RFC 4122 Version 4 Universally Unique Identifier (UUID v4) generated via standard `crypto.randomUUID()` (with a cryptographically secure Uint8Array fallback using `crypto.getRandomValues`).
- **Format:** `sess_<uuid-v4>` (e.g., `sess_8e0f7ca0-90cc-4969-9ce5-cfe02d277dbc`).
- **Prefix Purpose:** The `sess_` prefix provides unambiguous semantic tagging, preventing accidental transposition with event IDs while keeping the body completely opaque.
- **Privacy Guarantee:** Contains 122 bits of cryptographic entropy. Zero PII, zero timestamp leakage, zero device fingerprinting.

---

## 9. Event ID Generation

- **Algorithm:** RFC 4122 Version 4 UUID v4.
- **Format:** `evt_<uuid-v4>` (e.g., `evt_91eb4ea7-2b57-4812-8dbc-9fd026233c04`).
- **Collision Probability:** Negligible (1 in $2^{122}$), ensuring distinct event identities across all sessions.

---

## 10. Event Envelope / Schema

### JSON Schema (Draft-07):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SentinelGuardEventEnvelope",
  "type": "object",
  "properties": {
    "type": {
      "type": "string",
      "enum": ["TEST_EVENT"]
    },
    "event_type": {
      "type": "string",
      "enum": ["TEST_EVENT"]
    },
    "event_id": {
      "type": "string",
      "pattern": "^evt_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    },
    "session_id": {
      "type": "string",
      "pattern": "^sess_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    },
    "timestamp": {
      "type": "integer",
      "minimum": 1
    },
    "payload": {
      "type": "object",
      "additionalProperties": false
    }
  },
  "required": ["event_id", "session_id", "event_type", "timestamp"],
  "additionalProperties": true
}
```

### Concrete Example Payload:
```json
{
  "type": "TEST_EVENT",
  "event_type": "TEST_EVENT",
  "event_id": "evt_91eb4ea7-2b57-4812-8dbc-9fd026233c04",
  "session_id": "sess_8e0f7ca0-90cc-4969-9ce5-cfe02d277dbc",
  "timestamp": 1789021409516,
  "payload": {}
}
```

---

## 11. Data Flow

```
Webpage (http://localhost:3000/)
      │
      ▼
1. Content script injected (manifest.json: utils/identity.js, content/content.js)
      │
      ▼
2. SentinelIdentity.generateSessionId() -> sess_8e0f7ca0-...
      │
      ▼
3. SentinelIdentity.createEventEnvelope({ sessionId, eventType: "TEST_EVENT" })
   -> Assembles envelope with evt_91eb4ea7-..., timestamp, empty payload
      │
      ▼
4. chrome.runtime.sendMessage(envelope)
      │
      ▼
5. background/service-worker.js receives via chrome.runtime.onMessage
      │
      ▼
6. SentinelIdentity.validateEventEnvelope(envelope)
   - Checks format of event_id, session_id, event_type, timestamp
      │
      ▼
7. Service Worker DevTools Console:
   - [SentinelGuard] Event received.
   - [SentinelGuard] session_id: sess_8e0f7ca0-...
   - [SentinelGuard] event_id: evt_91eb4ea7-...
   - [SentinelGuard] timestamp: 1789021409516
```

---

## 12. Detailed Code Explanation

To satisfy the **Important Architectural Requirement** ("Avoid duplicating identity-generation logic in multiple files. Prefer a single clear source of truth"), a central utility was introduced:
- **`extension/utils/identity.js`**: Universal module implementing `SentinelIdentity`. Compatible with browser Window contexts, Worker/ServiceWorker contexts, and Node.js environments.
- **`extension/content/content.js`**: Consumes `SentinelIdentity` to bind the session ID and construct the event envelope.
- **`extension/background/service-worker.js`**: Imports `identity.js` via `importScripts("../utils/identity.js")` and consumes `validateEventEnvelope()` to verify integrity.

---

## 13. Line-by-Line Explanation of Important Implementation

### In `extension/utils/identity.js`:
- **`generateRawUUID()`**: Inspects `crypto.randomUUID()`. If present, calls it directly. If running in a legacy crypto environment, creates a 16-byte Uint8Array, seeds it with `crypto.getRandomValues()`, sets the RFC 4122 version (0100) and variant (10xx) bits, and formats hex strings.
- **`generateSessionId()`**: Appends `"sess_"` to the generated raw UUID.
- **`generateEventId()`**: Appends `"evt_"` to the generated raw UUID.
- **`createEventEnvelope(options)`**: Validates inputs, generates a new `event_id`, attaches the caller's `session_id`, sets `timestamp: Date.now()`, and returns the sealed envelope object.
- **`validateEventEnvelope(envelope)`**: Runs schema tests: verifies non-null object, uppercase string `event_type`, regex validation for `event_id` and `session_id`, and positive integer check for `timestamp`. Returns `{ valid: boolean, errors: string[] }`.

### In `extension/content/content.js`:
- **`const currentSessionId = SentinelIdentity.generateSessionId();`**: Binds the session identity to the lifetime of the content script execution in the tab.
- **`const testPayload = SentinelIdentity.createEventEnvelope({ ... });`**: Assembles the standardized envelope.
- **`chrome.runtime.sendMessage(testPayload, ...);`**: Dispatches the envelope over the IPC bus.

### In `extension/background/service-worker.js`:
- **`importScripts("../utils/identity.js");`**: Synchronously loads `SentinelIdentity` into the service worker global scope.
- **`const validation = SentinelIdentity.validateEventEnvelope(message);`**: Enforces gateway validation.
- **`if (!validation.valid) { ... }`**: Rejects invalid payloads immediately without processing.

---

## 14. Privacy and Security Considerations

1. **Zero PII:** Identifiers are 100% random and opaque. No correlation with usernames, emails, or IP addresses is possible.
2. **In-Memory Isolation:** Storing the session ID in content script memory ensures it is not accessible to JavaScript running on the host web page (isolated world protection).
3. **No Cross-Site Tracking:** Session IDs never leave the local origin and are destroyed upon page unload.

---

## 15. Threats and Misuse Considerations

- **Threat: Session Hijacking / Replay:**  
  *Mitigation:* Session IDs are only transferred over extension-internal IPC (`chrome.runtime`). No external page or network listener can sniff or inject session IDs.
- **Threat: Spoofed Malformed Events:**  
  *Mitigation:* The background service worker applies strict schema validation using regex and type guards. Malformed events are immediately rejected.
- **Threat: Cross-Tab Correlation:**  
  *Mitigation:* Tabs do not share session IDs. Each tab generates its own distinct ID.

---

## 16. Testing Strategy

1. **Automated Unit & Static Validation:**
   - Syntax validation via `node -c`.
   - Node.js execution testing for envelope creation and validation functions.
   - Negative testing verifying rejection of invalid envelopes.
   - Audit for forbidden listeners (`mousemove`, `keydown`, etc.).
2. **Manual Chrome Verification:**
   - Visual verification in DevTools console of webpage and background service worker.
   - Verification across page reload to observe session ID rollover.

---

## 17. Static Validation Results

| Test Case | Command | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| Syntax: `identity.js` | `node -c extension/utils/identity.js` | Exit code 0 | Clean exit | **PASS** |
| Syntax: `content.js` | `node -c extension/content/content.js` | Exit code 0 | Clean exit | **PASS** |
| Syntax: `service-worker.js` | `node -c extension/background/service-worker.js` | Exit code 0 | Clean exit | **PASS** |
| Manifest validity | `Get-Content manifest.json \| ConvertFrom-Json` | Valid JSON | Valid JSON | **PASS** |
| Identity generation | Node test script | Valid `sess_` and `evt_` UUIDs | Generated & verified | **PASS** |
| Envelope validation | Node test script | Valid envelope passes | `valid: true` | **PASS** |
| Envelope rejection | Node test script | Invalid IDs/timestamps rejected | Rejected with errors | **PASS** |
| Forbidden listener audit | PowerShell pattern match | 0 matches | 0 matches | **PASS** |
| Session & Event Identity (Chrome) | Manual Chrome DevTools test | Two distinct envelopes; unique session_id & event_id; session rollover on reload | Verified in Service Worker DevTools | **PASS — MANUALLY VERIFIED** |

---

## 18. Manual Verification Procedure (Google Chrome)

To manually verify Phase 3 in Google Chrome:

### Prerequisites:
Local test server running:
```powershell
python -m http.server 3000 --directory test-page
```

### Steps:
1. Open Chrome and navigate to `chrome://extensions/`.
2. Click the circular **Reload** icon on the **SentinelGuard** extension card.
3. Click the **service worker** link to open the background DevTools Console window.
4. Navigate to `http://localhost:3000/`.
5. Press `F12` on the webpage to open the webpage DevTools Console.
6. Verify output in both consoles.
7. **Reload the page (`F5`)** and observe the service worker console again: verify that `session_id` and `event_id` change to new random values.

---

## 19. Expected Output

### Webpage DevTools Console (`http://localhost:3000/`):
```
[SentinelGuard] Content script loaded.
[SentinelGuard] Test event sent.
```

### Service Worker DevTools Console:
```
[SentinelGuard] Service worker initialized.
[SentinelGuard] Event received.
[SentinelGuard] session_id: sess_8e0f7ca0-90cc-4969-9ce5-cfe02d277dbc
[SentinelGuard] event_id: evt_91eb4ea7-2b57-4812-8dbc-9fd026233c04
[SentinelGuard] timestamp: 1789021409516
```

### On Page Reload (`F5`):
```
[SentinelGuard] Event received.
[SentinelGuard] session_id: sess_<new-unique-id>
[SentinelGuard] event_id: evt_<new-unique-id>
[SentinelGuard] timestamp: <new-timestamp>
```

### 18.1. Actual Manual Verification Evidence (Google Chrome)

Manual verification was conducted in Google Chrome on the unpacked SentinelGuard extension with `python -m http.server 3000 --directory test-page` running.

#### Observed Results:
1. **Initial Page Load:**
   - Webpage DevTools Console displayed:
     ```
     [SentinelGuard] Content script loaded.
     [SentinelGuard] Test event sent.
     ```
   - Service Worker DevTools Console displayed:
     ```
     [SentinelGuard] Service worker initialized.
     [SentinelGuard] Event received.
     [SentinelGuard] session_id: sess_<uuid-1>
     [SentinelGuard] event_id: evt_<uuid-1>
     [SentinelGuard] timestamp: <timestamp-1>
     ```
2. **Page Reload (`F5`) — Session Rollover Verification:**
   - Webpage reloaded at `http://localhost:3000/`.
   - Content script re-executed in a fresh execution context.
   - Service Worker DevTools Console logged a second incoming event:
     ```
     [SentinelGuard] Event received.
     [SentinelGuard] session_id: sess_<uuid-2>
     [SentinelGuard] event_id: evt_<uuid-2>
     [SentinelGuard] timestamp: <timestamp-2>
     ```
3. **Verification Analysis:**
   - `session_id` changed from `sess_<uuid-1>` to `sess_<uuid-2>` (proving session lifecycle isolation per page observation and successful session rollover without persistent state).
   - `event_id` changed from `evt_<uuid-1>` to `evt_<uuid-2>` (proving unique event identity generation).
   - Both timestamps were positive, valid integers accurately reflecting dispatch times.
   - Gateway validation in `service-worker.js` accepted both envelopes with zero validation warnings or rejections.
   - Network isolation maintained: 0 outbound backend/telemetry calls.

---

## 20. Problems Encountered

- **Cross-Context Module Sharing:** Content scripts and Manifest V3 service workers use different module loading mechanisms in Chrome (content scripts execute in an isolated world and don't natively support ES import syntax without bundling; service workers support `importScripts`).
- **Fix Applied:** Implemented a Universal Module Definition (UMD) pattern in `extension/utils/identity.js` that binds to `globalThis` / `self`. Declared `utils/identity.js` in `manifest.json` before `content.js` for content scripts, and used `importScripts("../utils/identity.js")` in the service worker.

---

## 21. Fixes

1. Structured `extension/utils/identity.js` with fallback crypto random generation.
2. Updated `extension/manifest.json` to inject `utils/identity.js` before `content.js`.
3. Updated `extension/background/service-worker.js` with `importScripts`.

---

## 22. Final Repository Tree

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
│       ├── PHASE-02-MESSAGING.md
│       └── PHASE-03-SESSION-IDENTITY.md
├── extension/
│   ├── manifest.json
│   ├── background/
│   │   └── service-worker.js
│   ├── content/
│   │   └── content.js
│   ├── popup/
│   │   ├── popup.html
│   │   ├── popup.css
│   │   └── popup.js
│   └── utils/
│       └── identity.js
└── test-page/
    └── index.html
```

---

## 23. Explicit Non-Goals

The following items are **EXPLICIT NON-GOALS** for Phase 3:
- Capturing cursor movements or velocity.
- Capturing keystrokes or typing rhythms.
- Capturing form values, login credentials, or passwords.
- Transmitting data to a backend or Django server.
- Writing to permanent storage (`chrome.storage`, `localStorage`).
- Running machine learning or bot scoring logic.

---

## 24. Phase Limitations

- Events are purely synthetic test events (`TEST_EVENT`).
- No queueing or buffering mechanism exists yet; events are dispatched immediately.
- The service worker logs the event to the console and acknowledges it, but does not batch it.

---

## 25. Phase 4 Plan

Phase 4 will build upon the verified identity foundation:
- **Member 1:** Implement behavioral capture engines (mouse tracking and typing cadence) compliant with `docs/PRIVACY.md`.
- **Member 1:** Wrap captured telemetry into the Phase 3 event envelope and feed it into an in-memory buffer (`extension/utils/signal_buffer.js`).
- **Member 2:** Scaffold the Django backend endpoint (`POST /api/v1/events/`) to receive batched envelopes.

---

*Report updated: 2026-09-10*  
*Phase 3 Status: ✅ COMPLETE — MANUALLY VERIFIED*  
*Author: Member 1 (Browser Extension & Signal Capture)*
