# SentinelGuard — Integration Phase 5: Demo Login & Security Dashboard

## 1. Objective

Create a functional local demonstration system that showcases the complete SentinelGuard end-to-end flow:

```
Demo Login Page
    ↓
Chrome Extension behavioral telemetry
    ↓
Django /api/events/
    ↓
ML risk scoring (RandomForestClassifier)
    ↓
Server-authoritative adaptive security
    ↓
ALLOW / OTP / BLOCK
    ↓
OTP verification when required
    ↓
Login result
    ↓
Security dashboard / audit visibility
```

## 2. Existing Architecture Reused

| Component | Source | Reused As-Is |
|-----------|--------|-------------|
| Chrome Extension (Manifest V3) | `extension/` | ✅ |
| Mouse behavioral telemetry (10 features) | `extension/content/content.js` | ✅ |
| Session/event identity | `extension/utils/identity.js` | ✅ |
| Service worker (backend relay) | `extension/background/service-worker.js` | ✅ |
| Django Event API | `POST /api/events/` | ✅ |
| ML feature extraction | `backend/ml/features.py` | ✅ |
| ML inference (RandomForest) | `backend/ml/inference.py` | ✅ |
| ML scoring integration | `backend/detection/ml_scoring.py` | ✅ |
| Adaptive security policy | `backend/security/services.py` | ✅ |
| Login endpoint | `POST /api/security/login/` | ✅ |
| OTP verification endpoint | `POST /api/security/verify-otp/` | ✅ |
| SecurityLog model | `backend/security/models.py` | ✅ |
| Protection ON/OFF toggle | `extension/popup/` | ✅ |

No existing Phase 1–4 functionality was modified.

## 3. Demo Login Implementation

### Location

`test-page/login.html` — served at `http://localhost:3000/login.html`

### Features

- SentinelGuard branding with dark theme
- Username input (pre-filled with `demo-user`)
- Password input (visual only — **never sent** to backend, telemetry, or logs)
- Login button → `POST /api/security/login/`
- Visual state machine: idle → analyzing → allowed / OTP required / blocked / error
- Hidden OTP verification panel (shown on 202 response)
- OTP input → `POST /api/security/verify-otp/`
- Navigation links to dashboard and test page

### Request payload

```json
{
  "session_id": "sess_<uuid>",
  "username": "demo-user"
}
```

The client sends **only** `session_id` and `username`. No risk_score, tier, action, is_bot, or behavioral features.

## 4. Session Identity Mechanism

### Challenge

The extension generates `currentSessionId` in `content.js` at page load, but this variable is isolated in the content script's execution context and not directly accessible to page JavaScript.

### Solution: `window.postMessage` bridge

1. `content.js` listens for `{ type: "SentinelGuard:RequestSessionId" }` messages on the window.
2. When received, it responds with `{ type: "SentinelGuard:SessionId", sessionId: currentSessionId }`.
3. The login page sends the request on load and listens for the response.
4. If the extension doesn't respond within 1.5 seconds, the login page generates a standalone `sess_<uuid>` and displays a visible warning.

### Security properties

- Only the opaque UUID is shared — no internal extension state or API surface is exposed.
- The bridge uses `window.postMessage` on the same origin, which is the standard content-script ↔ page communication mechanism.
- The session ID contains zero PII.

## 5. Login API Flow

```
User clicks "Sign In"
    ↓
POST /api/security/login/
  { session_id, username }
    ↓
Server looks up Session → Score
    ↓
risk_score < 0.30 → HTTP 200 { action: "ALLOW" }
0.30 ≤ risk_score < 0.70 → HTTP 202 { action: "OTP", challenge_id }
risk_score ≥ 0.70 → HTTP 403 { action: "BLOCK" }
No score → fallback 0.50 → HTTP 202 OTP
```

The server is **strictly authoritative**. Client-supplied risk scores are ignored and rejected.

## 6. OTP Flow

```
HTTP 202 received → OTP panel shown
    ↓
User enters 6-digit code from backend console
    ↓
POST /api/security/verify-otp/
  { challenge_id, otp }
    ↓
HTTP 200 → verified, login allowed
HTTP 401 → wrong code (attempts decremented)
HTTP 403 → locked (max 3 attempts) or expired
HTTP 400 → invalid request
```

- OTP lifetime: 5 minutes
- Maximum attempts: 3
- OTP hash: Django PBKDF2 (not plaintext)
- Development-only: OTP code printed to Django console

## 7. Dashboard Architecture

### Location

`test-page/dashboard/` — served at `http://localhost:3000/dashboard/`

### Stack

Pure HTML/CSS/JS — no framework dependencies.

### Components

1. **Stats Cards**: Total Events, Security Decisions, Allowed, OTP Challenges, Blocked
2. **Decision Distribution Bar**: Visual proportional bar showing ALLOW/OTP/BLOCK ratios
3. **Recent Security Logs Table**: Action, Risk Score, Session (truncated), Username, Reason, Timestamp
4. **Connection Status Indicator**: Shows connected/disconnected state
5. **Manual Refresh Button**: Fetches latest data on click

## 8. Dashboard Endpoints

### `GET /api/security/stats/`

Returns aggregate statistics.

```json
{
  "stats": {
    "total_events": 42,
    "total_decisions": 15,
    "allowed": 8,
    "otp": 5,
    "blocked": 2
  }
}
```

### `GET /api/security/logs/`

Returns the 50 most recent SecurityLog entries.

```json
{
  "logs": [
    {
      "id": "uuid",
      "session_id": "sess_...",
      "username_attempted": "demo-user",
      "risk_score": 0.1234,
      "action_taken": "ALLOW",
      "reason": "Authoritative behavioral evaluation",
      "timestamp": "2026-09-24T01:00:00Z"
    }
  ]
}
```

### Security properties

- **GET only** — POST returns 405 Method Not Allowed
- **Read-only** — no data is modified
- **Excludes**: `ip_address`, `otp_hash`, `otp_code`, `password`, raw coordinates

## 9. Security & Privacy Guarantees

| Guarantee | Status |
|-----------|--------|
| Server-authoritative risk scoring | ✅ Enforced |
| Password never sent to backend/telemetry | ✅ Enforced |
| No raw mouse coordinates transmitted | ✅ Enforced |
| No OTP code/hash exposed via API | ✅ Enforced |
| Dashboard is read-only | ✅ Enforced (GET only, 405 on POST) |
| Protection OFF stops all telemetry | ✅ Preserved |
| Existing validation rules unchanged | ✅ Verified |
| OTP hashing uses Django PBKDF2 | ✅ Enforced |

## 10. Tests

### New Dashboard Tests (10)

| # | Test | Validates |
|---|------|-----------|
| 23 | `test_23_stats_returns_200` | Stats endpoint basic functionality |
| 24 | `test_24_logs_returns_200` | Logs endpoint basic functionality |
| 25 | `test_25_stats_is_get_only` | Stats rejects POST (405) |
| 26 | `test_26_logs_is_get_only` | Logs rejects POST (405) |
| 27 | `test_27_logs_exclude_ip_address` | No IP address in response |
| 28 | `test_28_logs_exclude_otp_hash` | No OTP hash in response |
| 29 | `test_29_logs_exclude_password` | No password/otp_code in response |
| 30 | `test_30_logs_exclude_raw_coordinates` | No x/y/coordinates in response |
| 31 | `test_31_stats_reflect_action_counts` | ALLOW/OTP/BLOCK counts accurate |
| 32 | `test_32_stats_total_events_counts_event_table` | Event count from Event table |

### Total Test Suite

- Detection (API + ML): 23 tests
- Security (Policy + OTP + Audit): 22 tests
- Dashboard: 10 tests
- **Total: 55 tests — all passing**

## 11. Manual Testing Procedure

### Scenario 1 — Human-like Behavior → ALLOW

1. Start backend: `cd backend && python manage.py runserver 127.0.0.1:8000`
2. Start test server: `python -m http.server 3000 --directory test-page`
3. Load extension in Chrome (chrome://extensions → Load unpacked → `extension/`)
4. Enable Protection ON in popup
5. Navigate to `http://localhost:3000/login.html`
6. Move mouse naturally around the page
7. Click "Sign In"
8. Verify ALLOW response (if ML score < 0.30)
9. Check dashboard at `http://localhost:3000/dashboard/`

### Scenario 2 — OTP Flow

1. Use a session with risk score in [0.30, 0.70) range, or a session without any Score (fallback 0.50)
2. Click "Sign In" → expect 202 OTP Required
3. Check Django console for development OTP code
4. Enter OTP in verification panel
5. Verify 200 SUCCESS response
6. Confirm SecurityLog shows original risk score (not 0.0)
7. Check dashboard for updated logs

### Scenario 3 — Bot-like Behavior → BLOCK

1. Use a session with high risk score (≥ 0.70)
2. Click "Sign In" → expect 403 BLOCKED
3. Confirm dashboard records the BLOCK entry

### Scenario 4 — Client Spoof Attempt

1. Open browser DevTools → Console
2. Send: `fetch("http://127.0.0.1:8000/api/security/login/", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({session_id: "<high-risk-session>", risk_score: 0.0, action: "ALLOW"}) })`
3. Verify server still returns BLOCK based on authoritative Score

### Scenario 5 — Protection OFF

1. Toggle Protection OFF in extension popup
2. Move mouse on the page
3. Verify no MOUSE_BEHAVIOR events in Service Worker console
4. Verify no new events in Django console

## 12. Known Limitations

> [!NOTE]
> **This is a local demonstration system.** The following limitations are by design for the demo scope:

1. **Not production authentication** — The login page simulates a login flow but does not perform real user authentication or session management.

2. **Synthetic ML training data** — The RandomForestClassifier is trained on synthetic data generated by `ml/dataset.py`. Real-world bot detection performance would require production behavioral data and retraining.

3. **Probabilistic behavioral signals** — Mouse behavioral features are probabilistic indicators, not definitive proof of malicious intent. The ML model outputs a risk probability, not a binary determination.

4. **Dashboard endpoints are unauthenticated** — In production, `/api/security/stats/` and `/api/security/logs/` would require admin authentication and authorization. The current demo allows anonymous read access for local development convenience.

5. **Session ID linkage** — The session ID bridge via `window.postMessage` requires the extension to be installed and loaded on the page. Without the extension, the login page uses a standalone session ID that has no behavioral telemetry linked to it, so the server will use the fallback risk score (0.50 → OTP).

6. **Single-tab session scope** — Each page load generates a new session ID. There is no cross-tab session persistence in the current architecture.

7. **CORS is open for development** — `CORS_ALLOW_ALL_ORIGINS = True` is configured for local development convenience. Production deployment must restrict allowed origins.
