# Integration Phase 2 Report — Extension to Backend Connectivity

**Project:** SentinelGuard — AI-Driven Bot & Credential-Stuffing Defense System  
**Phase:** Integration Phase 2 — Extension to Backend Connectivity  
**Branch:** `integration`  
**Date:** 2026-09-23  
**Status:** COMPLETE & VERIFIED  

---

## 1. Objective

The primary objective of Integration Phase 2 is to bridge the air gap between the Chrome Extension signal capture layer and the Django REST Framework backend foundation established in Phase 1.

Specifically, this phase:
- Routes validated `MOUSE_BEHAVIOR` telemetry event envelopes from the background Service Worker to Django's ingestion API (`POST http://127.0.0.1:8000/api/events/`).
- Enforces architectural isolation: Content scripts never communicate directly over external network protocols; all network transmissions are mediated exclusively by the background Service Worker.
- Adds strictly scoped host permissions to `extension/manifest.json` (`http://127.0.0.1:8000/*`).
- Handles server responses cleanly (`201 CREATED`, `200 DUPLICATE`, `400 BAD REQUEST`, and network connection failures) without unhandled exceptions or infinite retry loops.
- Strictly adheres to protection state synchronization: When protection is toggled OFF, zero network requests leave the browser and zero event rows are created in SQLite.
- Preserves the zero-PII privacy guarantee: Transmits only derived kinematic features; strictly zero coordinates (`x`, `y`), zero keystrokes, and zero passwords ever leave the client.

---

## 2. Architecture Before

Prior to Integration Phase 2:
```text
Browser Page (http://localhost:3000/)
    ↓
Content Script (content.js)
    ↓ (50 ms throttling, max 25 samples)
Feature Extraction (SentinelMouseFeatures.calculateFeatures)
    ↓
Event Envelope (SentinelIdentity.createEventEnvelope)
    ↓
Chrome Runtime Messaging (chrome.runtime.sendMessage)
    ↓
Service Worker (service-worker.js)
    ↓
[AIR GAP / DISCONNECTED — Local console logging only]
```
The Django backend (`http://127.0.0.1:8000/api/events/`) was fully operational and tested, but the extension never transmitted data across the network.

---

## 3. Architecture After

With Integration Phase 2 complete:
```text
Browser Page (http://localhost:3000/)
    ↓
Content Script (content.js)
    ↓ (50 ms throttling, max 25 samples)
Feature Extraction (SentinelMouseFeatures.calculateFeatures)
    ↓ (10 privacy-conscious kinematic features)
Event Envelope (SentinelIdentity.createEventEnvelope)
    ↓ (session_id, event_id, timestamp, payload)
Chrome Runtime Messaging (chrome.runtime.sendMessage)
    ↓
Service Worker (service-worker.js)
    ↓ (Validates envelope structure & feature bounds)
    ↓ (Verifies Protection ON in memory & storage)
HTTP POST (fetch)
    ↓ (Headers: Content-Type: application/json)
Django Event Ingestion (http://127.0.0.1:8000/api/events/)
    ↓ (EventInSerializer validates schema, bounds, & zero-PII rules)
    ↓ (Session get_or_create & idempotency check on event_id)
SQLite Database (`backend/db.sqlite3` -> `detection_event` table)
```

---

## 4. Files Changed

| File | Status | Description |
| :--- | :--- | :--- |
| `extension/manifest.json` | Modified | Added `"host_permissions": ["http://127.0.0.1:8000/*"]` to permit cross-origin network transmission from the background Service Worker strictly to the local Django backend. |
| `extension/background/service-worker.js` | Modified | Implemented `sendEventToBackend(envelope)` to transmit validated `MOUSE_BEHAVIOR` envelopes over HTTP POST to `http://127.0.0.1:8000/api/events/`, with concise status logging and non-blocking error handling. |
| `docs/reports/INTEGRATION-PHASE-02-EXTENSION-BACKEND.md` | Created | Comprehensive integration, testing, and verification documentation. |

---

## 5. Manifest Changes

### Manifest Excerpt:
```json
  "permissions": [
    "storage"
  ],
  "host_permissions": [
    "http://127.0.0.1:8000/*"
  ],
```

### Rationale:
In Chrome Extensions Manifest V3, cross-origin `fetch()` requests initiated from background Service Workers require explicit declaration under `host_permissions`.
- **Minimal Privilege Principle**: Rather than requesting broad access patterns such as `<all_urls>` or `http://*/*`, permissions are restricted strictly to port 8000 on `127.0.0.1`.
- **Content Script Isolation**: No network permissions were granted to content scripts; content scripts remain completely isolated from network access.

---

## 6. HTTP Contract

### Request:
```http
POST /api/events/ HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "type": "MOUSE_BEHAVIOR",
  "event_type": "MOUSE_BEHAVIOR",
  "event_id": "evt_4a71b126-5b32-4d43-8557-0a955745e69e",
  "session_id": "sess_81cf8021-3e4f-4d9c-a5d6-848cfbe2594a",
  "timestamp": 1727100456123,
  "payload": {
    "movement_count": 25,
    "total_distance": 142.85,
    "movement_duration": 650,
    "average_velocity": 0.22,
    "maximum_velocity": 0.58,
    "velocity_variance": 0.015,
    "direction_change_count": 4,
    "average_direction_change": 0.38,
    "path_efficiency": 0.82,
    "straightness_ratio": 0.89
  }
}
```

### Response Handling:
- **`201 CREATED`**:
  - Logged: `[SentinelGuard] Backend ACK: 201`
  - Action: Event successfully ingested and committed to SQLite.
- **`200 OK` (Duplicate `event_id`)**:
  - Logged: `[SentinelGuard] Backend duplicate: 200`
  - Action: Non-fatal acknowledgment. Event is discarded by backend to prevent duplication.
- **`400 BAD REQUEST`**:
  - Logged: `[SentinelGuard] Backend rejected event: 400`
  - Action: Warning logged. Malformed or invalid events are rejected.
- **Network Failure (e.g. Django offline, connection refused)**:
  - Logged: `[SentinelGuard] Backend unavailable.`
  - Action: Warning logged. Service worker continues executing normally without crashing.

---

## 7. Protection Behavior

The protection toggle acts as an absolute circuit-breaker across all layers:

1. **Content Script Layer**:
   - When protection is OFF, passive mouse listeners drop all cursor points immediately.
   - Any buffered points are purged (`movementBuffer = []`).
   - Any active timeout is cancelled (`clearTimeout(idleTimer)`).
   - Zero runtime messages are dispatched to the Service Worker.

2. **Service Worker Layer**:
   - `service-worker.js` checks `isProtectionEnabled` synchronously.
   - `service-worker.js` queries `chrome.storage.local.get(["protectionEnabled"])` as an asynchronous defense-in-depth pre-flight check.
   - `sendEventToBackend()` verifies `if (!isProtectionEnabled) return;` immediately before calling `fetch()`.

3. **Verification Flow**:
   - **Protection ON**: Mouse movement -> Feature extraction -> Envelope created -> Service Worker sends POST -> SQLite row inserted (`201 CREATED`).
   - **Protection OFF**: Mouse movement -> No features extracted -> No messages sent -> No network calls made -> SQLite row count remains unchanged.
   - **Protection ON Again**: Normal telemetry and backend transmission resume cleanly.

---

## 8. Error Handling

- **Asynchronous Execution**: Network transmission runs asynchronously via `fetch()` and does not block content script event collection or popup interactions.
- **No Unhandled Rejections**: Network errors (such as `ECONNREFUSED` or DNS resolution failures) are wrapped in `try/catch` and logged with `[SentinelGuard] Backend unavailable.`
- **Zero Crash Guarantee**: Extension remains responsive and fully operational even if Django is stopped or restarting.
- **No Infinite Retries**: Failed events are dropped cleanly without spamming network loops. Duplicate events are handled idempotently by backend unique constraints on `event_id`.

---

## 9. Privacy Behavior

- **Strict Zero-PII Policy**:
  - Only statistical and kinematic features are transmitted (`movement_count`, `average_velocity`, `path_efficiency`, etc.).
  - The request body NEVER contains:
    - Raw coordinates (`x`, `y`, `coordinates`, `raw`)
    - Keystrokes or typing inputs
    - Passwords, usernames, or form field values
    - Page text or DOM snippets
    - Cookies, tokens, or IP addresses
- **Backend Schema Enforcement**: The Django `EventInSerializer` rejects any request where the JSON payload contains forbidden keys (`x`, `y`, `coordinates`, `password`, `key`, `text`, `raw`).

---

## 10. Automated Tests

### 1. Django Backend API Test Suite (`backend/detection/tests.py`):
Command:
```powershell
python manage.py test detection
```
Result:
```text
Ran 11 tests in 0.062s - OK
- test_health_check_returns_ok: 200 OK
- test_valid_mouse_behavior_event: 201 Created & DB persisted
- test_duplicate_event_id: 200 DUPLICATE
- test_invalid_session_id: 400 Bad Request
- test_invalid_event_id: 400 Bad Request
- test_invalid_event_type: 400 Bad Request
- test_invalid_non_numeric_feature: 400 Bad Request
- test_boolean_feature_rejected_as_non_numeric: 400 Bad Request
- test_missing_required_event_fields: 400 Bad Request
- test_raw_coordinates_and_sensitive_keys_prohibited: 400 Bad Request
- test_valid_test_event: Phase 3 backwards compatibility verified
```

### 2. Service Worker Network Logic Test Suite (`scratch/test_service_worker_logic.js`):
Command:
```powershell
node scratch/test_service_worker_logic.js
```
Result:
```text
=== Service Worker Logic & Backend Contract Test ===
--- TEST 1: Valid Event Transmission (Protection ON) ---
[SentinelGuard] Sending MOUSE_BEHAVIOR event to backend.
[SentinelGuard] Backend ACK: 201
TEST 1 PASSED: Received HTTP 201 ACK from live Django backend.

--- TEST 2: Duplicate Event Submission ---
[SentinelGuard] Sending MOUSE_BEHAVIOR event to backend.
[SentinelGuard] Backend duplicate: 200
TEST 2 PASSED: Received HTTP 200 DUPLICATE from live Django backend.

--- TEST 3: Validation Error Handling (400) ---
[SentinelGuard] Sending MOUSE_BEHAVIOR event to backend.
[SentinelGuard] Backend rejected event: 400
TEST 3 PASSED: Correctly logged 400 Bad Request rejection.

--- TEST 4: Protection OFF Prevents Transmission ---
[SentinelGuard][DEBUG] Aborting backend transmission: protection OFF
TEST 4 PASSED: Network transmission aborted when protection is OFF.

--- TEST 5: Backend Offline Resilience ---
[SentinelGuard] Sending MOUSE_BEHAVIOR event to backend.
[SentinelGuard] Backend unavailable.
TEST 5 PASSED: Backend network failure caught gracefully without crashing.

--- TEST 6: Zero PII & Coordinate Privacy Invariant ---
TEST 6 PASSED: Serialized envelope strictly contains zero coordinates and zero credentials.

=== ALL 6 SERVICE WORKER LOGIC TESTS PASSED ===
```

---

## 11. Manual Verification Checklist

Follow these steps for interactive manual verification in Google Chrome:

### Prerequisites:
1. Ensure Django backend is running:
   ```powershell
   cd backend
   python manage.py runserver 127.0.0.1:8000
   ```
2. Verify backend health:
   ```text
   GET http://127.0.0.1:8000/api/health/ -> {"status": "ok"}
   ```
3. Load unpacked extension in Chrome (`chrome://extensions` -> Load unpacked -> select `extension/`).
4. Open the test page: `http://localhost:3000/`.
5. Open the Service Worker DevTools: click `service worker` link on `chrome://extensions`.

### Step A: Protection ON Verification
1. Move the mouse across `http://localhost:3000/` for ~2 seconds.
2. In the Service Worker console, observe:
   ```text
   [SentinelGuard] Mouse behavior event received.
   [SentinelGuard] Sending MOUSE_BEHAVIOR event to backend.
   [SentinelGuard] Backend ACK: 201
   ```
3. In the Django terminal, observe:
   ```text
   "POST /api/events/ HTTP/1.1" 201
   ```
4. Query SQLite to verify the row exists:
   ```powershell
   python -c "import sqlite3; conn = sqlite3.connect('backend/db.sqlite3'); print(conn.cursor().execute('SELECT event_id, event_type FROM detection_event ORDER BY id DESC LIMIT 1').fetchone()); conn.close()"
   ```

### Step B: Protection OFF Verification
1. Click the SentinelGuard extension icon in Chrome toolbar to open the popup.
2. Toggle the protection switch to **OFF**. (Status shows `PAUSED / OFF`).
3. Move the mouse continuously on `http://localhost:3000/` for 10–15 seconds.
4. Verify in Service Worker console: **Zero** `Sending MOUSE_BEHAVIOR event to backend.` logs appear.
5. Verify in Django terminal: **Zero** `POST /api/events/` requests appear.
6. Verify in SQLite: **Zero** new rows are added.

### Step C: Protection ON Resumption Verification
1. Open the extension popup again and toggle protection back to **ON**. (Status shows `ACTIVE / ON`).
2. Move the mouse on `http://localhost:3000/` for ~2 seconds.
3. Verify in Service Worker console: `[SentinelGuard] Backend ACK: 201` resumes.
4. Verify in SQLite: A new row is successfully inserted.

### Step D: Backend Offline Resilience
1. Stop the Django development server (Ctrl+C in terminal).
2. Move the mouse on `http://localhost:3000/`.
3. In Service Worker console, observe:
   ```text
   [SentinelGuard] Sending MOUSE_BEHAVIOR event to backend.
   [SentinelGuard] Backend unavailable.
   ```
4. Confirm Chrome extension and Service Worker do not crash.
5. Restart Django server (`python manage.py runserver 127.0.0.1:8000`).
6. Move mouse again -> observe `Backend ACK: 201` resumes immediately.

### Step E: Privacy Inspection
1. In Service Worker DevTools Network tab, inspect the payload of `POST /api/events/`.
2. Confirm the JSON body contains only:
   `type`, `event_type`, `event_id`, `session_id`, `timestamp`, and `payload` (10 numerical features).
3. Confirm zero instances of `x`, `y`, `coordinates`, `password`, or sensitive text.

---

## 12. Exact Observed Results

- **Health Endpoint**: Returned HTTP 200 `{"status": "ok"}`.
- **Valid Event Transmission**: Service Worker dispatched POST request and received HTTP 201 `ACK`.
- **Database Persistence**: SQLite database stored the event row with exact session and event identifiers.
- **Zero Coordinate Leakage**: Verified that no raw `(x, y)` coordinate objects exist in the database or serialized payload.
- **Protection OFF Behavior**: Verified that toggling protection OFF prevents network transmissions and database writes.
- **Resilience**: Verified graceful handling of duplicate event IDs (HTTP 200 `DUPLICATE`) and offline server states without service worker crashes.

---

## 13. Known Limitations

- **No Machine Learning Classification Yet**: Events are ingested and stored in SQLite, but the `Score` model is not yet evaluated.
- **No Adaptive Security Yet**: `Decision` engine (`ALLOW`, `OTP`, `BLOCK`) is not yet invoked on ingested events.
- **No Dashboard Visualization Yet**: Admin dashboard for monitoring real-time sessions is not yet connected.
- **Mouse Telemetry Only**: Typing biometrics and credential-field focus tracking are intentionally deferred to future integration phases.

---

## 14. Next Integration Phase

**Integration Phase 3: Machine Learning Model Integration & Risk Scoring**
- Implement / integrate Member 2's trained ML classifier.
- Extract ingested mouse behavioral features from `detection_event` rows.
- Compute risk score (0–100) and assign security tiers (`allow`, `otp`, `block`) into the `Score` table.
