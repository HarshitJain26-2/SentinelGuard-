# SentinelGuard — Behavioral Event Data Schema

> **STATUS: PROVISIONAL**
> **Requires explicit agreement between Member 1 (Extension) and Member 2 (Backend/ML) before implementation.**
> This schema is a proposal authored by Member 1. It is NOT finalized. Member 2 must review, revise, and sign off on this document before any API integration code is written.
> Fields marked `[TBD]` require Member 2 input.

---

## Purpose

This document defines the proposed structure of the **behavioral event payload** that Member 1's browser extension will transmit to Member 2's Django backend API endpoint. It is the primary coordination artifact between Members 1 and 2.

---

## API Contract Status

| Item | Status |
|------|--------|
| Endpoint URL | **PROVISIONAL** — e.g., `POST /api/v1/events/` |
| HTTP Method | **PROVISIONAL** — POST |
| Content-Type | **PROVISIONAL** — `application/json` |
| Authentication | **TBD** — Member 2 must specify (API key? JWT? None for prototype?) |
| Response format | **TBD** — Member 2 must specify |
| CORS origin | **TBD** — Member 2 must whitelist `chrome-extension://<extension-id>` |
| Rate limiting | **TBD** — Member 2 must specify |

> **Coordination requirement:** Member 1 and Member 2 must agree on all [TBD] items before Phase 1 integration work begins. This agreement must be recorded by updating this document with status changed from PROVISIONAL to AGREED.

---

## Top-Level Payload Structure

```json
{
  "schema_version": "1.0",
  "session_id": "<uuid-v4>",
  "extension_version": "0.1.0",
  "captured_at": "<ISO-8601 UTC timestamp>",
  "page_origin": "<protocol + hostname only — no path>",
  "signals": {
    "mouse": { ... },
    "keyboard": { ... },
    "form_interaction": { ... }
  },
  "metadata": {
    "capture_duration_ms": 12400,
    "event_count": 183,
    "extension_enabled": true
  }
}
```

---

## Field Definitions

### Root Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | `string` | Yes | Schema version for backward compatibility. Currently `"1.0"`. |
| `session_id` | `string (UUIDv4)` | Yes | Randomly generated per login-page session. NOT linked to user identity. Ephemeral — discarded after transmission. |
| `extension_version` | `string` | Yes | Semver string of the extension version that generated the payload. |
| `captured_at` | `string (ISO-8601)` | Yes | UTC timestamp of when the payload was assembled for transmission. |
| `page_origin` | `string` | Yes | Protocol and hostname only (e.g., `"https://example.com"`). **Never includes path, query string, or fragment.** |
| `signals` | `object` | Yes | Container for all behavioral signal sub-objects. |
| `metadata` | `object` | Yes | Container for payload-level metadata. |

---

### `signals.mouse`

Captures mouse movement and click behavior.

```json
"mouse": {
  "movement_samples": [
    { "x": 412, "y": 308, "t_ms": 1000 },
    { "x": 416, "y": 311, "t_ms": 1032 },
    { "x": 421, "y": 319, "t_ms": 1064 }
  ],
  "click_events": [
    { "x": 512, "y": 400, "t_ms": 4520, "target_type": "text_field" },
    { "x": 512, "y": 450, "t_ms": 7830, "target_type": "password_field" },
    { "x": 350, "y": 520, "t_ms": 14200, "target_type": "submit_button" }
  ],
  "total_distance_px": 843.2,
  "total_movement_time_ms": 13200
}
```

| Field | Type | Description | Privacy Note |
|-------|------|-------------|-------------|
| `movement_samples[].x` | `integer` | Horizontal cursor position in viewport pixels | ✅ Permitted |
| `movement_samples[].y` | `integer` | Vertical cursor position in viewport pixels | ✅ Permitted |
| `movement_samples[].t_ms` | `integer` | Milliseconds elapsed since page load / session start | ✅ Permitted |
| `click_events[].x` | `integer` | Click x coordinate | ✅ Permitted |
| `click_events[].y` | `integer` | Click y coordinate | ✅ Permitted |
| `click_events[].t_ms` | `integer` | Click timestamp (ms from session start) | ✅ Permitted |
| `click_events[].target_type` | `string enum` | One of: `"text_field"`, `"password_field"`, `"submit_button"`, `"other"` | ✅ Field type only — never field content |
| `total_distance_px` | `float` | Sum of Euclidean distances between consecutive movement samples | ✅ Derived aggregate |
| `total_movement_time_ms` | `integer` | Total duration of mouse movement recording | ✅ Permitted |

**Sampling rate for `movement_samples`:** PROVISIONAL — suggested every 32ms (≈30 Hz). Member 2 must confirm sufficient granularity for the ML model.

---

### `signals.keyboard`

Captures typing rhythm via timing metadata only. **Key values are never recorded.**

```json
"keyboard": {
  "username_field": {
    "keystroke_count": 12,
    "timings": [
      { "dwell_ms": 87, "flight_ms": 112 },
      { "dwell_ms": 94, "flight_ms": 78 },
      { "dwell_ms": 103, "flight_ms": 130 }
    ],
    "total_entry_duration_ms": 2840,
    "backspace_count": 1,
    "paste_occurred": false
  },
  "password_field": {
    "keystroke_count": 10,
    "timings": [
      { "dwell_ms": 91, "flight_ms": 95 },
      { "dwell_ms": 88, "flight_ms": 101 }
    ],
    "total_entry_duration_ms": 1920,
    "backspace_count": 0,
    "paste_occurred": false
  }
}
```

| Field | Type | Description | Privacy Note |
|-------|------|-------------|-------------|
| `keystroke_count` | `integer` | Number of keystroke events captured in this field | ✅ Count only |
| `timings[].dwell_ms` | `integer` | Time (ms) between `keydown` and `keyup` for a single keystroke | ✅ Timing only — no key identity |
| `timings[].flight_ms` | `integer` | Time (ms) between previous `keyup` and current `keydown` (inter-key gap) | ✅ Timing only — no key identity |
| `total_entry_duration_ms` | `integer` | Time from first keydown to last keyup in this field | ✅ Permitted |
| `backspace_count` | `integer` | Number of backspace/delete events detected (count only) | ✅ Count only — does not reveal what was corrected |
| `paste_occurred` | `boolean` | Whether a paste event occurred in this field | ✅ Permitted — boolean flag only, not paste content |

> **CRITICAL PRIVACY CONSTRAINT:**
> The `timings` array contains **only millisecond durations**. It does **not** contain, and must **never** contain, the `event.key` value, `event.code`, or any other character-identifying data. The entire keyboard signal section is timing metadata only.

---

### `signals.form_interaction`

Captures the sequence and timing of interactions with the login form overall.

```json
"form_interaction": {
  "field_focus_sequence": [
    { "field_type": "text_field", "focus_t_ms": 500, "blur_t_ms": 3340 },
    { "field_type": "password_field", "focus_t_ms": 3800, "blur_t_ms": 5720 }
  ],
  "submission_t_ms": 14200,
  "time_to_first_interaction_ms": 1240,
  "total_session_duration_ms": 14200,
  "tab_visible_throughout": true
}
```

| Field | Type | Description | Privacy Note |
|-------|------|-------------|-------------|
| `field_focus_sequence[].field_type` | `string enum` | `"text_field"` or `"password_field"` | ✅ Field type only |
| `field_focus_sequence[].focus_t_ms` | `integer` | Time (ms from session start) when field received focus | ✅ Permitted |
| `field_focus_sequence[].blur_t_ms` | `integer` | Time (ms from session start) when field lost focus | ✅ Permitted |
| `submission_t_ms` | `integer` | Time (ms from session start) when form was submitted | ✅ Permitted |
| `time_to_first_interaction_ms` | `integer` | Delay from page load to first user interaction | ✅ Permitted |
| `total_session_duration_ms` | `integer` | Total duration from session start to form submission | ✅ Permitted |
| `tab_visible_throughout` | `boolean` | Whether the browser tab remained visible during the session (using Page Visibility API) | ✅ Permitted |

---

### `metadata`

Payload-level metadata about the capture session.

| Field | Type | Description |
|-------|------|-------------|
| `capture_duration_ms` | `integer` | Total duration of active signal capture |
| `event_count` | `integer` | Total number of raw events captured before batching |
| `extension_enabled` | `boolean` | Whether the extension was enabled throughout (should always be `true` if payload is being sent) |

---

## Fields That Will NEVER Appear in the Payload

The following fields are explicitly prohibited. Any code that adds them to the payload is a critical privacy violation:

| Prohibited Field | Why |
|---|---|
| `event.key` / any key value | Reveals which character was typed |
| `event.code` / physical key code | Can be used to reconstruct typed text |
| `password_field.value` | Credential data — hard prohibited |
| `username_field.value` | Credential data — hard prohibited |
| `clipboard_content` | Private user data |
| `user_agent` raw string | Fingerprinting risk (may be added as simplified category if ML model needs it — TBD) |
| `ip_address` | Not available to extension; belongs to backend |
| `page_url_path` | May contain sensitive identifiers |

---

## Transmission Protocol (PROVISIONAL)

```
Method:   POST
Endpoint: https://<backend-host>/api/v1/events/   [TBD — Member 2 must confirm]
Headers:
  Content-Type: application/json
  X-Extension-Version: <extension_version>
  Authorization: <TBD — Member 2 must specify auth mechanism>

Body: <JSON payload as described above>

Expected response:
  HTTP 200 OK   → payload accepted
  HTTP 400      → malformed payload (extension should log, not retry)
  HTTP 429      → rate limited (extension should back off)
  HTTP 500      → server error (extension should log, not retry in this session)
```

---

## Coordination Requirements

**Before Member 1 writes any API call code:**

- [ ] Member 2 must review and approve (or revise) this schema.
- [ ] Member 2 must specify the final endpoint URL.
- [ ] Member 2 must specify the authentication mechanism.
- [ ] Member 2 must confirm sampling rates sufficient for ML model.
- [ ] Member 2 must confirm which fields are required vs. optional for the model.
- [ ] Member 2 must add `chrome-extension://` to Django CORS allow-list.
- [ ] Both members must update this document's status from PROVISIONAL to AGREED.

**Sign-off block (to be completed before Phase 1 integration):**

```
Member 1 sign-off: ________________  Date: ________
Member 2 sign-off: ________________  Date: ________
```

---

---

## Phase 3 Internal Event Envelope (IMPLEMENTED)

While the top-level payload structure above defines the **provisional future backend transmission format** (PLANNED), Phase 3 establishes the internal **Runtime IPC Event Envelope** used between the content script and background service worker (`extension/utils/identity.js`):

```json
{
  "type": "TEST_EVENT",
  "event_type": "TEST_EVENT",
  "event_id": "evt_<uuid-v4>",
  "session_id": "sess_<uuid-v4>",
  "timestamp": 1789021409516,
  "payload": {}
}
```

| Field | Type | Status | Description |
|---|---|---|---|
| `event_id` | `string (evt_<uuid>)` | **IMPLEMENTED (Phase 3)** | Unique RFC 4122 v4 identifier generated per event instance |
| `session_id` | `string (sess_<uuid>)` | **IMPLEMENTED (Phase 3)** | Opaque RFC 4122 v4 identifier generated per page observation lifecycle |
| `event_type` | `string` | **IMPLEMENTED (Phase 3)** | Uppercase event discriminator (`TEST_EVENT`) |
| `timestamp` | `integer` | **IMPLEMENTED (Phase 3)** | Milliseconds since Unix epoch (`Date.now()`) |
| `payload` | `object` | **IMPLEMENTED (Phase 3)** | Event-specific data container (empty in Phase 3) |

---

## Phase 4 Mouse Behavioral Telemetry Internal Event (IMPLEMENTED)

In Phase 4, the internal Runtime IPC event stream introduces real behavioral signal extraction for mouse dynamics (`MOUSE_BEHAVIOR`). 

**Scope Status:**
- **IMPLEMENTED (Phase 4):** Content script feature extraction, bounded in-memory sampling buffer (max 25 points, 50 ms / 20 Hz throttled), ephemeral coordinate discard, and service worker validation gateway.
- **PLANNED (Future Phases):** Backend HTTP POST transmission, event batching over network, server-side feature store, ML classification model, bot-risk scoring, typing rhythm telemetry, and adaptive OTP challenge.

> [!IMPORTANT]
> **Data Tier Separation (Raw Temporary Data vs. Derived Telemetry):**
> - **RAW TEMPORARY DATA:** Cursor positions (`clientX`, `clientY`) and timestamps are captured exclusively inside an ephemeral, in-memory array (`movementBuffer`, max 25 points) in `content.js`. They are **never** persisted to storage, **never** logged, and **never** transmitted across runtime IPC. The buffer is wiped immediately after feature computation.
> - **DERIVED TELEMETRY:** The background service worker receives **only** the 10 compact derived mathematical metrics (`movement_count`, `total_distance`, `movement_duration`, `average_velocity`, `maximum_velocity`, `velocity_variance`, `direction_change_count`, `average_direction_change`, `path_efficiency`, `straightness_ratio`). The service worker never receives or reconstructs raw coordinates.

### Internal Event Envelope (`MOUSE_BEHAVIOR`)

```json
{
  "type": "MOUSE_BEHAVIOR",
  "event_type": "MOUSE_BEHAVIOR",
  "event_id": "evt_4a712f20-b49d-4e2a-89aa-09633e9d41b2",
  "session_id": "sess_8e0f7ca0-90cc-4969-9ce5-cfe02d277dbc",
  "timestamp": 1789024800123,
  "payload": {
    "movement_count": 25,
    "total_distance": 642.1523,
    "average_velocity": 0.5137,
    "maximum_velocity": 1.4820,
    "velocity_variance": 0.1245,
    "direction_change_count": 3,
    "average_direction_change": 0.4215,
    "path_efficiency": 0.8842,
    "straightness_ratio": 0.9120,
    "movement_duration": 1250
  }
}
```

### Feature Dictionary Specification

| Feature Key | Type | Unit | Range | Mathematical / Algorithmic Definition | Edge Case / Fallback Handling |
|---|---|---|---|---|---|
| `movement_count` | `integer` | count | $\ge 2$ | Number of sampled movement points $N$ within the active gesture window. | Windows with $N < 2$ are discarded before emission. |
| `total_distance` | `float` | pixels (px) | $\ge 0.0$ | Cumulative Euclidean distance: $\sum_{i=1}^{N-1} \sqrt{(x_{i+1}-x_i)^2 + (y_{i+1}-y_i)^2}$. | $0.0$ if coordinates are stationary or identical. |
| `average_velocity` | `float` | px / ms | $\ge 0.0$ | Mean trajectory speed: $\frac{\text{total\_distance}}{\text{movement\_duration}}$. | $0.0$ if duration $\le 0$ or distance is $0.0$. |
| `maximum_velocity` | `float` | px / ms | $\ge 0.0$ | Maximum instantaneous segment speed: $\max_i \left( \frac{\Delta d_i}{\max(\Delta t_i, 1)} \right)$. | $0.0$ if no segment has positive duration. |
| `velocity_variance` | `float` | $(\text{px}/\text{ms})^2$ | $\ge 0.0$ | Sample variance of segment velocities: $\frac{1}{M} \sum_{i=1}^M (v_i - \bar{v})^2$. | $0.0$ if fewer than 2 segments exist. |
| `direction_change_count` | `integer` | count | $\ge 0$ | Count of consecutive segment transitions where angular deflection $> \frac{\pi}{6}$ rad ($30^\circ$). | $0$ if trajectory is straight, stationary, or $N < 3$. |
| `average_direction_change` | `float` | radians | $[0.0, \pi]$ | Mean absolute angular deflection across all valid segment transitions. | $0.0$ if fewer than 2 non-zero displacement segments exist. |
| `path_efficiency` | `float` | ratio | $[0.0, 1.0]$ | Ratio of direct Euclidean chord displacement to total distance: $\frac{\|P_N - P_1\|}{\text{total\_distance}}$. | $0.0$ if total distance is $0.0$. Clamped to $[0.0, 1.0]$. |
| `straightness_ratio` | `float` | ratio | $[0.0, 1.0]$ | Complement of normalized maximum orthogonal chord deviation: $1 - \frac{d_{\text{max}}}{\|P_N - P_1\|}$. | Special case: If start and end coordinates are identical ($P_1 == P_N$, closed loop), ratio is defined as $0.0$. Clamped to $[0.0, 1.0]$. |
| `movement_duration` | `integer` | ms | $\ge 0$ | Total elapsed time: $t_N - t_1$. | $0$ if timestamps are identical or non-positive. |

> [!NOTE]
> **Signal Distinction:** These 10 features represent raw behavioral kinematic signals. None of these features individually classify an interaction as human or bot; bot vs. human classification belongs exclusively to Member 2's planned ML inference layer.

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 0.1 (PROVISIONAL) | 2026-09-09 | Member 1 | Initial draft for Member 2 review |
| 0.2 (IMPLEMENTED)  | 2026-09-10 | Member 1 | Added Phase 3 Internal Runtime IPC Event Envelope |
| 0.3 (IMPLEMENTED)  | 2026-09-23 | Member 1 | Added Phase 4 Mouse Behavioral Telemetry Internal Event Schema |

---

*Last updated: Phase 4 — Mouse Behavioral Telemetry*
*Primary author: Member 1*
*Required reviewer: Member 2*

