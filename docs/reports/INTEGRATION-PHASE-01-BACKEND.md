# Integration Phase 1 Report — Backend Foundation

**Project:** SentinelGuard — AI-Driven Bot & Credential-Stuffing Defense System  
**Phase:** Integration Phase 1 — Backend Foundation  
**Branch:** `integration`  
**Date:** 2026-09-23  
**Status:** COMPLETE & VERIFIED  

---

## 1. Objective

The objective of Integration Phase 1 is to establish a robust, reliable, and secure Django REST Framework backend foundation that connects the browser extension telemetry pipeline to persistent server-side storage.

Specifically, this phase:
- Configures CORS and allowed host boundaries for local cross-origin development.
- Implements a dedicated health check endpoint (`GET /api/health/`).
- Validates the incoming extension event envelope (`POST /api/events/`) matching Phase 3 identity standards and Phase 4 mouse behavioral telemetry.
- Enforces strict zero-PII privacy constraints (prohibiting raw mouse coordinates, passwords, keystrokes, and arbitrary text).
- Ensures idempotent ingestion by safely handling duplicate `event_id` submissions.
- Preserves the existing relational database structure (`Session`, `Event`, `Score`, `Decision`) for upcoming ML and adaptive security integration without prematurely introducing unverified ML logic.

---

## 2. Existing Backend Architecture

Prior to Integration Phase 1, the backend contained:
- **Django 5.0.6 & Django REST Framework 3.15.2**: Web application and REST API framework.
- **`detection` app**:
  - `Session` model: Identifies browsing sessions via client-generated `session_id` (`sess_<uuid-v4>`).
  - `Event` model: Stores ingested telemetry envelopes with `client_timestamp`, `event_type`, and `payload` JSON.
  - `Score` model: One-to-one relationship with `Session` holding `risk_score` (0–100), `tier` (`allow`, `otp`, `block`), and `reasons` JSON. (Scaffold reserved for Member 2 ML model).
  - `Decision` model: Foreign key to `Session` logging `action_taken` (`allow`, `otp`, `block`) with audit timestamps. (Scaffold reserved for Member 3 adaptive security).
  - `EventCreateView`: API view for `POST /api/events/`.
  - `EventInSerializer` and `EventOutSerializer`: Basic input/output serializers.
- **Database**: SQLite (`db.sqlite3`). Initial migration `0001_initial.py` already matched models.

---

## 3. Changes Made

1. **CORS Configuration (`backend/sentinelguard/settings.py`)**:
   - Added `corsheaders` to `INSTALLED_APPS`.
   - Added `corsheaders.middleware.CorsMiddleware` to `MIDDLEWARE` in the highest precedence position (before `SecurityMiddleware` and `CommonMiddleware`).
   - Configured `CORS_ALLOW_ALL_ORIGINS = True` with an explicit development/demo warning comment stating that production deployments must restrict origins to trusted domains and extension IDs.

2. **Host Security Configuration (`backend/sentinelguard/settings.py`)**:
   - Configured `ALLOWED_HOSTS = ["localhost", "127.0.0.1"]` to prevent unauthorized host header manipulation.

3. **Backend Health Check Endpoint (`backend/detection/views.py` & `backend/detection/urls.py`)**:
   - Implemented `HealthCheckView` responding to `GET /api/health/` with HTTP 200 `{"status": "ok"}`.
   - Registered `path("health/", HealthCheckView.as_view(), name="health-check")` under the `api/` route tree.

4. **Enhanced Envelope & Payload Validation (`backend/detection/serializers.py`)**:
   - Accepted the extension envelope format, including optional top-level `type` along with `event_type`, `event_id`, `session_id`, `timestamp`, `payload`, and `device_label`.
   - Stripped whitespace and enforced non-empty validation on `event_id` and `session_id`.
   - Validated `event_type` against permitted types (`MOUSE_BEHAVIOR`, `TEST_EVENT`).
   - For `MOUSE_BEHAVIOR`:
     - Prohibited forbidden keys (`x`, `y`, `coordinates`, `password`, `key`, `text`, `raw`).
     - Enforced that all 10 expected mouse behavioral features are finite numeric values (excluding booleans).
     - Applied physical bounds validation: `movement_count >= 2`, non-negative distances, durations, and velocities, and ratios between 0.0 and 1.0.

5. **Automated Test Suite (`backend/detection/tests.py`)**:
   - Replaced empty test file with an 11-test automated suite verifying health checks, valid ingestion, duplicate handling, field validation, and privacy prohibitions.

---

## 4. API Contract

### Ingestion Endpoint: `POST /api/events/`

#### Request Headers:
```http
Content-Type: application/json
```

#### Request Envelope:
```json
{
  "type": "MOUSE_BEHAVIOR",
  "event_type": "MOUSE_BEHAVIOR",
  "event_id": "evt_b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e",
  "session_id": "sess_a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "timestamp": 1727100123456,
  "payload": {
    "movement_count": 25,
    "total_distance": 100.0,
    "movement_duration": 500,
    "average_velocity": 0.2,
    "maximum_velocity": 0.5,
    "velocity_variance": 0.01,
    "direction_change_count": 3,
    "average_direction_change": 0.4,
    "path_efficiency": 0.8,
    "straightness_ratio": 0.9
  }
}
```

#### Success Response (HTTP 201 Created):
```json
{
  "status": "ACK",
  "event": {
    "event_id": "evt_b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e",
    "session_id": "sess_a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
    "event_type": "MOUSE_BEHAVIOR",
    "client_timestamp": 1727100123456,
    "payload": {
      "movement_count": 25,
      "total_distance": 100.0,
      "movement_duration": 500,
      "average_velocity": 0.2,
      "maximum_velocity": 0.5,
      "velocity_variance": 0.01,
      "direction_change_count": 3,
      "average_direction_change": 0.4,
      "path_efficiency": 0.8,
      "straightness_ratio": 0.9
    },
    "received_at": "2026-09-23T18:08:55.322636Z"
  }
}
```

#### Duplicate Submission Response (HTTP 200 OK):
```json
{
  "status": "DUPLICATE"
}
```

#### Validation Error Response (HTTP 400 Bad Request):
```json
{
  "status": "REJECTED",
  "errors": {
    "payload": [
      "Raw coordinates or sensitive fields (x, y) are strictly prohibited."
    ]
  }
}
```

---

## 5. Health Endpoint

### Endpoint: `GET /api/health/`

#### Request:
```http
GET /api/health/ HTTP/1.1
Host: 127.0.0.1:8000
```

#### Response (HTTP 200 OK):
```json
{
  "status": "ok"
}
```

---

## 6. Validation Rules

| Field | Requirement | Rejection Rule |
| :--- | :--- | :--- |
| `event_id` | String, max 100 chars | Empty, missing, or whitespace-only |
| `session_id` | String, max 100 chars | Empty, missing, or whitespace-only |
| `event_type` | Must be `MOUSE_BEHAVIOR` or `TEST_EVENT` | Unsupported event type string |
| `timestamp` | Positive integer (epoch milliseconds) | `< 1`, non-integer, or missing |
| `payload` | Must be JSON object for `MOUSE_BEHAVIOR` | Non-dict object or null |
| `payload` privacy | Strict zero-PII check | Keys matching `x`, `y`, `coordinates`, `password`, `key`, `text`, `raw` |
| `movement_count` | Integer `>= 2` | `< 2` or non-numeric |
| Kinematic distances/velocities | Non-negative numeric | `< 0.0` or non-numeric |
| `path_efficiency`, `straightness_ratio` | Floating point ratio | `< 0.0`, `> 1.0`, or non-numeric |
| Numeric values | Must satisfy `math.isfinite()` | `NaN`, `Infinity`, `-Infinity`, Booleans |

---

## 7. Database Behavior

- **Session Upsert**: When an event is received, `Session.objects.get_or_create(session_id=...)` automatically registers the session if not already existing.
- **Idempotency Guard**: Before saving, the backend queries `Event.objects.filter(event_id=event_id).exists()`. If already present, HTTP 200 `{"status": "DUPLICATE"}` is returned, preventing primary key collisions or duplicate data rows.
- **Schema Preservation**: The `Score` and `Decision` tables remain intact in migrations and models, with foreign keys to `Session`.
- **Zero Raw Coordinates**: Only aggregated mathematical features reside in SQLite JSON fields.

---

## 8. Tests

Ran Django automated test suite:
```powershell
python manage.py test detection
```

### Results:
```text
Creating test database for alias 'default'...
...........
----------------------------------------------------------------------
Ran 11 tests in 0.119s

OK
Destroying test database for alias 'default'...
Found 11 test(s).
System check identified no issues (0 silenced).
```

### Verified Test Cases:
1. `test_health_check_returns_ok`: Confirms `GET /api/health/` returns HTTP 200 `{"status": "ok"}`.
2. `test_valid_mouse_behavior_event`: Confirms valid `MOUSE_BEHAVIOR` event creates `Session` and `Event` rows and returns HTTP 201 `ACK`.
3. `test_duplicate_event_id`: Confirms duplicate submissions return HTTP 200 `DUPLICATE` without duplicating records.
4. `test_invalid_session_id`: Confirms blank/whitespace `session_id` returns HTTP 400 `REJECTED`.
5. `test_invalid_event_id`: Confirms blank/whitespace `event_id` returns HTTP 400 `REJECTED`.
6. `test_invalid_event_type`: Confirms unknown event types return HTTP 400 `REJECTED`.
7. `test_invalid_non_numeric_feature`: Confirms non-numeric string values for telemetry features return HTTP 400 `REJECTED`.
8. `test_boolean_feature_rejected_as_non_numeric`: Confirms boolean values (e.g., `True`) for numeric features return HTTP 400 `REJECTED`.
9. `test_missing_required_event_fields`: Confirms missing `event_id`, `session_id`, or `timestamp` returns HTTP 400 `REJECTED`.
10. `test_raw_coordinates_and_sensitive_keys_prohibited`: Confirms forbidden keys (`x`, `y`, `coordinates`, `password`, `key`, `text`) return HTTP 400 `REJECTED`.
11. `test_valid_test_event`: Confirms backwards compatibility with Phase 3 `TEST_EVENT`.

---

## 9. Manual Verification

Started local Django server on `http://127.0.0.1:8000/`.

### Verification Steps & Responses:

1. **Health Check**:
   - Request: `GET http://127.0.0.1:8000/api/health/`
   - Response: `HTTP 200 {"status":"ok"}`

2. **Realistic `MOUSE_BEHAVIOR` Event Ingestion**:
   - Payload:
     ```json
     {
       "type": "MOUSE_BEHAVIOR",
       "event_type": "MOUSE_BEHAVIOR",
       "event_id": "evt_manual_verify_001",
       "session_id": "sess_manual_verify_001",
       "timestamp": 1727100123456,
       "payload": {
         "movement_count": 25,
         "total_distance": 100.0,
         "movement_duration": 500,
         "average_velocity": 0.2,
         "maximum_velocity": 0.5,
         "velocity_variance": 0.01,
         "direction_change_count": 3,
         "average_direction_change": 0.4,
         "path_efficiency": 0.8,
         "straightness_ratio": 0.9
       }
     }
     ```
   - Response: `HTTP 201 {"status":"ACK","event":{"event_id":"evt_manual_verify_001", ...}}`

3. **Duplicate Submission**:
   - Re-sent the identical payload.
   - Response: `HTTP 200 {"status":"DUPLICATE"}`

4. **Direct SQLite Database Query**:
   - Queried table `detection_event`:
     - Row found: `('evt_manual_verify_001', 1, 'MOUSE_BEHAVIOR', '{"movement_count": 25, ...}')`
     - Verified `CONTAINS RAW COORDS: False`.

---

## 10. Security & Privacy Considerations

- **Strict Zero-PII Policy**: Backend serializers strictly validate and block any payload containing coordinates (`x`, `y`, `coordinates`) or credentials (`password`, `key`, `text`, `raw`).
- **No Coordinate Logging**: Neither views nor serializers log mouse coordinates or user interactions.
- **Allowed Hosts Boundary**: Limited to `localhost` and `127.0.0.1` during development.
- **CORS Scope**: Enabled for development. Explicit warning documented in `settings.py` for future production hardening.

---

## 11. Files Changed

- `backend/sentinelguard/settings.py`: Added `corsheaders` to `INSTALLED_APPS`, `CorsMiddleware` to `MIDDLEWARE`, `CORS_ALLOW_ALL_ORIGINS`, and `ALLOWED_HOSTS`.
- `backend/detection/views.py`: Added `HealthCheckView`.
- `backend/detection/urls.py`: Added `health/` route.
- `backend/detection/serializers.py`: Strengthened validation rules, forbidden key checks, numeric checks, and allowed event types.
- `backend/detection/tests.py`: Added comprehensive unit test suite covering health and events APIs.
- `docs/reports/INTEGRATION-PHASE-01-BACKEND.md`: This comprehensive verification report.

---

## 12. Commands Required to Run Backend

```powershell
# Navigate to backend directory
cd backend

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Run automated tests
python manage.py test detection

# Start local development server
python manage.py runserver 127.0.0.1:8000
```

---

## 13. Known Limitations

- **No ML Classification Yet**: Risk score calculation is not implemented; `Score` table rows are not populated yet.
- **No Adaptive Security Yet**: `Decision` table records (`allow`, `otp`, `block`) are not generated yet.
- **Extension Connection**: The Chrome extension does not yet transmit events over the network (extension `fetch()` will be integrated in Phase 2).
- **CORS Permissive in Dev**: `CORS_ALLOW_ALL_ORIGINS` is enabled for local development across test ports.

---

## 14. Next Integration Phase

**Integration Phase 2: Extension-to-Backend Connectivity**
- Safely enable background service worker transmission of validated event envelopes via `fetch()` to `http://127.0.0.1:8000/api/events/`.
- Verify end-to-end data flow: Chrome browser interaction -> Content script feature extraction -> Service worker envelope packaging -> Backend REST API ingestion -> SQLite storage.
