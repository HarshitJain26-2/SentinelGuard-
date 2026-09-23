# Integration Phase 4 Report — Adaptive Security Integration

**Project:** SentinelGuard — AI-Driven Bot & Credential-Stuffing Defense System  
**Phase:** Integration Phase 4 — Adaptive Security Integration  
**Branch:** `integration`  
**Date:** 2026-09-24  
**Status:** COMPLETE & VERIFIED  

---

## 1. Objective

The objective of Integration Phase 4 is to establish an authoritative, server-driven Adaptive Security Policy Engine that evaluates probabilistic risk scores (0.0 to 1.0) produced by the Phase 3 ML Risk Engine and applies risk-based access control decisions:
- **`ALLOW`**: Low risk (< 0.30) — immediate login access granted.
- **`OTP`**: Medium risk [0.30, 0.70) or unrated sessions — step-up multi-factor authentication challenge required.
- **`BLOCK`**: High risk (>= 0.70) — access denied immediately to neutralize automated bots.

Furthermore, Phase 4 ports and refactors Member 3's prototype security code, eliminates a critical client-side trust vulnerability, integrates persistent audit logging, and enforces time-bound, attempt-throttled OTP challenge verification.

---

## 2. Existing Member 3 Implementation Reviewed

Prior to Phase 4, the repository contained prototype security code on `origin/Anuja` in separate directories (`backend/security/` and an abandoned `backend/adaptive_security/`).

Key findings from inspecting `origin/Anuja`:
- Included early scaffolds for `SecurityLog` and `OTPChallenge` models.
- Contained basic threshold definitions: `LOW_RISK_THRESHOLD = 0.30`, `HIGH_RISK_THRESHOLD = 0.70`.
- Stored plaintext 6-digit OTP codes in the database.
- Lacked integration with the central extension session architecture (`detection.models.Session`, `Event`, `Score`).
- Suffered from a critical security vulnerability where the client supplied the risk score.

---

## 3. What Was Ported

- **Policy Thresholds**: Preserved the 0.30 and 0.70 boundary thresholds.
- **`SecurityLog`**: Ported and adapted into `backend/security/models.py`, capturing `session`, `username_attempted`, `ip_address`, `risk_score`, `action_taken`, `reason`, and timestamp.
- **`OTPChallenge` Lifecycle**: Preserved 6-digit random codes, 5-minute expirations, and a 3-attempt maximum.
- **API Views & Endpoints**: Adapted `LoginAttemptView` and `VerifyOTPView` into the current `sentinelguard` routing structure.

---

## 4. What Was Changed & Refactored

1. **Integrated with Central Project**:
   - Built the `security` app directly within the current project (`backend/security/`).
   - Registered `security` in `INSTALLED_APPS` and mounted routes under `/api/security/`.
   - Avoided creating duplicate projects (`backend/backend/`).
2. **Session & Score Linkage**:
   - `SecurityLog` and `OTPChallenge` now reference `detection.models.Session`.
   - Evaluated decisions update `detection.models.Decision` and sync with `Score.tier`.
3. **Cryptographic OTP Hashing**:
   - Plaintext OTP storage was replaced with salted SHA-256 hashes (`OTPChallenge.set_otp(code)`).
   - The challenge's unique UUID is used as a cryptographic salt.
4. **Idempotent Challenge Management**:
   - Previous unverified challenges for the same session are invalidated when a new challenge is issued.

---

## 5. Critical Security Flaw Fixed

### The Flaw in the Old Prototype:
In `origin/Anuja:backend/security/views.py`:
```python
# VULNERABLE CODE (DO NOT USE)
risk_score = float(request.data.get("risk_score", 0.0))
```
The prototype accepted `risk_score` directly from the client's HTTP request body. Any bot script could trivially bypass detection simply by sending:
```json
{
  "username": "admin",
  "risk_score": 0.0
}
```

### The Fix in Integration Phase 4:
Client-provided risk parameters (`risk_score`, `tier`, `action`, `is_bot`) are **strictly ignored**.
The server retrieves the authoritative score exclusively from the server-side database:
```text
Client Request: { "session_id": "sess_..." }
       ↓
Server queries database: Session.objects.get(session_id=...)
       ↓
Server reads authoritative score: session.score.risk_score
       ↓
Server applies policy: evaluate_policy_action(risk_score)
```
**Mandatory Security Test**: A dedicated test (`test_8_client_provided_risk_score_is_ignored_and_db_authoritative_block`) verifies that when a client sends `risk_score: 0.0` for a session with a database score of `0.92`, the server returns HTTP 403 `BLOCK`.

---

## 6. Current Architecture

```text
Browser Extension / Client
       ↓ HTTP POST
Django Ingestion (/api/events/)
       ↓
Event & ML Risk Engine (/backend/ml/)
       ↓
Authoritative Score (detection_score table)
       ↓
Login Attempt (/api/security/login/)
       ↓
Security Service (/backend/security/services.py)
       ├── Session Lookup (Authoritative DB Score)
       ├── Policy Evaluation:
       │     ├── risk < 0.30        -> ALLOW (HTTP 200)
       │     ├── 0.30 <= risk < 0.70 -> OTP (HTTP 202) -> OTPChallenge created
       │     └── risk >= 0.70       -> BLOCK (HTTP 403)
       ├── Audit Logging -> SecurityLog table
       └── Sync with Decision table
```

---

## 7. Risk Thresholds & Boundary Policy

Evaluations are performed on exact floating-point values without pre-rounding:

| Risk Score ($R$) | Action | HTTP Status | Description |
| :--- | :---: | :---: | :--- |
| $R < 0.30$ | **`ALLOW`** | `200 OK` | Low risk; authenticated human baseline |
| $0.30 \le R < 0.70$ | **`OTP`** | `202 ACCEPTED` | Medium risk or unrated; step-up challenge required |
| $R \ge 0.70$ | **`BLOCK`** | `403 FORBIDDEN` | High risk; automated bot signature detected |

### Boundary Behavior:
- `0.00` → `ALLOW`
- `0.299999` → `ALLOW`
- `0.30` → `OTP`
- `0.699999` → `OTP`
- `0.70` → `BLOCK`
- `1.00` → `BLOCK`

---

## 8. No-Score Fallback Behavior

When a login request is made for a `session_id` that has no server-generated score (e.g. browsing telemetry has not yet completed or was interrupted):
1. The server **never** trusts client-supplied risk scores.
2. The server **never** invents or persists a fake `Score` row in `detection_score`.
3. The server safely applies the documented neutral fallback:
   - **Fallback Risk**: `0.50`
   - **Action**: `OTP` (HTTP 202)
   - **Reason**: `"Server risk score unavailable - defaulting to step-up OTP challenge (fallback policy)"`
4. The fallback reason is explicitly recorded in `SecurityLog`.

---

## 9. OTP Challenge Lifecycle

- **Generation**: Cryptographically secure 6-digit integer (`secrets.randbelow(900000) + 100000`).
- **Storage**: Salted SHA-256 hash using the challenge UUID as salt.
- **Expiration**: Exactly 5 minutes from creation (`expires_at = created_at + 5 min`).
- **Throttling**: Maximum 3 verification attempts.
  - Attempt 1 failure: `HTTP 401 Unauthorized`, `attempts_remaining: 2`.
  - Attempt 2 failure: `HTTP 401 Unauthorized`, `attempts_remaining: 1`.
  - Attempt 3 failure: `HTTP 403 Forbidden`, `attempts_remaining: 0`, challenge locked.
- **Single-Use**: Once verified (`is_verified = True`), the challenge cannot be reused (`HTTP 400 Bad Request`).
- **Expired Rejection**: Challenges submitted after expiration return `HTTP 400 Bad Request`.

---

## 10. Security Audit Logging (`SecurityLog`)

Every login attempt and OTP verification creates an immutable `SecurityLog` record:
- `session`: Foreign key to `detection.Session`.
- `session_id_raw`: Preserves submitted string even if session was unregistered.
- `username_attempted`: Identifier string.
- `ip_address`: Captured from `HTTP_X_FORWARDED_FOR` or `REMOTE_ADDR`.
- `risk_score`: Authoritative score evaluated (0.0 to 1.0).
- `action_taken`: `ALLOW`, `OTP`, or `BLOCK`.
- `reason`: Contributing explainability factors.
- `timestamp`: UTC creation timestamp.

**Privacy Guarantee**: No passwords, raw coordinates, form inputs, session cookies, or plaintext OTPs are ever written to `SecurityLog`.

---

## 11. API Endpoints

### 1. Login Attempt Endpoint
- **URL**: `POST /api/security/login/`
- **Request Body**:
  ```json
  {
    "session_id": "sess_81cf8021-3e4f-4d9c-a5d6-848cfbe2594a",
    "username": "demo_user"
  }
  ```
- **Responses**:
  - **ALLOW (HTTP 200 OK)**:
    ```json
    {
      "action": "ALLOW",
      "risk_score": 0.0652,
      "message": "Access granted."
    }
    ```
  - **OTP (HTTP 202 Accepted)**:
    ```json
    {
      "action": "OTP",
      "risk_score": 0.4500,
      "challenge_id": "ac442b9d-3f5a-4cdb-afed-0f66890b597b",
      "expires_at": "2026-09-24T19:32:04.123456+00:00",
      "message": "OTP step-up authentication required."
    }
    ```
  - **BLOCK (HTTP 403 Forbidden)**:
    ```json
    {
      "action": "BLOCK",
      "risk_score": 0.9500,
      "message": "Access blocked due to high behavioral risk."
    }
    ```

### 2. OTP Verification Endpoint
- **URL**: `POST /api/security/verify-otp/`
- **Request Body**:
  ```json
  {
    "challenge_id": "ac442b9d-3f5a-4cdb-afed-0f66890b597b",
    "otp": "576695"
  }
  ```
- **Responses**:
  - **Success (HTTP 200 OK)**:
    ```json
    {
      "status": "SUCCESS",
      "action": "ALLOW",
      "message": "OTP verified successfully."
    }
    ```
  - **Incorrect OTP (HTTP 401 Unauthorized)**:
    ```json
    {
      "status": "FAILED",
      "error": "Invalid OTP code.",
      "attempts_remaining": 2
    }
    ```
  - **Lockout (HTTP 403 Forbidden)**:
    ```json
    {
      "status": "FAILED",
      "error": "Maximum verification attempts exceeded. Challenge locked.",
      "attempts_remaining": 0
    }
    ```

---

## 12. Automated Tests

Ran complete backend test suite:
```powershell
python manage.py test
```
**Results: 44 tests, 0 failures, 0 errors (0.413s)**.

### Test Coverage Breakdown:
- **Detection & ML Tests (23 tests)**:
  - Health check, event validation, CORS, raw coordinate prohibition, idempotent deduplication, ML dataset generation, feature extraction & ordering, model loading & inference bounds, fault isolation.
- **Security Policy & OTP Tests (21 tests)**:
  - `test_1` through `test_7`: Policy boundary conditions (0.0, 0.299999, 0.30, 0.45, 0.699999, 0.70, 0.85, 1.0).
  - `test_8`: Mandatory security test: client sending `risk_score: 0.0` on bot session is blocked (HTTP 403).
  - `test_9`: Client sending `risk_score: 0.99` on human session is allowed (HTTP 200).
  - `test_10`: Session without score uses 0.50 fallback without creating fake DB score.
  - `test_11`: OTP creation validates expiration, zero attempts, and salted hash storage.
  - `test_12`: Expired challenge rejection.
  - `test_13`: Wrong OTP increments attempt counter and returns remaining attempts.
  - `test_14`: 3 consecutive failed attempts lock challenge permanently (HTTP 403).
  - `test_15`: Successful OTP verification returns HTTP 200 ALLOW.
  - `test_16`: Reusing a verified OTP is rejected (HTTP 400).
  - `test_17`: Submitting correct OTP after expiration is rejected (HTTP 400).
  - `test_18`: `SecurityLog` records decisions and reasons for auditability.
  - `test_19`: Duplicate login attempts handled idempotently.
  - `test_20`: Missing or whitespace `session_id` returns HTTP 400.
  - `test_21`: Missing `challenge_id` or `otp` on verify returns HTTP 400.

---

## 13. Security Considerations

- **Server-Side Authority**: The client never dictates risk scores, tiers, or security actions.
- **Timing & Privacy**: OTP hashes prevent offline database compromise from exposing usable codes.
- **Attempt Throttling**: 3-attempt cap prevents brute-forcing 6-digit codes ($10^6$ space).
- **Time Boxing**: 5-minute lifetime limits replay and interception windows.

---

## 14. Development-Only OTP Behavior

To facilitate manual testing and demo verification without an external SMS/email gateway:
- The server logs the generated OTP to the terminal console during development:
  ```text
  [DEVELOPMENT ONLY] SentinelGuard OTP Generated:
    Session:      sess_...
    Challenge ID: ac442b9d-3f5a-4cdb-afed-0f66890b597b
    Code:         576695
    Expires:      19:27:04 UTC
  ```
- **Plaintext OTP is never returned in API responses** or stored in database tables.

---

## 15. Known Limitations

- **Email/SMS Gateway**: OTPs are printed to the console rather than dispatched via SMS/email providers (Twilio, SendGrid), which is standard for local demo phases.
- **UI Integration**: Frontend login modal and OTP challenge input screens belong to the upcoming Integration Phase 5.
