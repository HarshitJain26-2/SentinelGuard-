# SentinelGuard
### AI-Driven Bot & Credential-Stuffing Defense System

---

## Problem Statement

Credential-stuffing attacks — where attackers replay large lists of stolen username/password pairs against login forms — are among the most prevalent and damaging threats facing modern web applications. Traditional CAPTCHA and IP-rate-limiting defenses are increasingly bypassed by sophisticated bots that mimic human behavior at the network layer.

**SentinelGuard** addresses this by shifting detection from *network signals* to *behavioral signals*: the way a real human physically interacts with a login form is measurably different from any automated script or bot, even one designed to look human.

---

## Solution Overview

SentinelGuard is a four-component system that:

1. **Captures** fine-grained behavioral signals from the browser during login interactions (mouse, keyboard timing, form events) — invisibly and without storing credentials.
2. **Analyzes** those signals server-side using a machine learning model that produces a real-time bot-risk score.
3. **Acts** on that score with adaptive security responses — step-up OTP challenges, session flags, or soft blocks — proportional to the detected risk level.
4. **Reports** risk events and session decisions to a centralized admin dashboard for monitoring and tuning.

---

## Team Responsibilities

| Member | Responsibility | Primary Technologies |
|--------|---------------|----------------------|
| **Member 1** | Browser Extension + Behavioral Signal Capture | Chrome Manifest V3, JS, Service Worker |
| **Member 2** | Django Backend + ML Risk Model | Python, Django REST Framework, scikit-learn / PyTorch |
| **Member 3** | Adaptive Security Logic + OTP System | Django middleware, TOTP/email OTP |
| **Member 4** | Admin Dashboard + Demo Login Page | React / HTML+JS, Chart.js or similar |

---

## Current Development Status

```
PHASE 0 — COMPLETE   ✅  Repository inspection & documentation foundation
PHASE 1 — COMPLETE   ✅  Browser extension scaffold (Member 1)
PHASE 2 — COMPLETE   ✅  Extension runtime messaging pipeline (Member 1)
PHASE 3 — COMPLETE   ✅  Session & event identity foundation (Member 1)
PHASE 4 — IMPLEMENTED ⏳  Mouse behavioral telemetry (Member 1) [PENDING MANUAL VERIFICATION]
PHASE 5 — PENDING    ⏳  Integration & end-to-end testing (all members)
```

> **Current Implementation Note:** The Chrome Manifest V3 browser extension scaffold, runtime messaging pipeline, session/event identity envelope, and **Mouse Behavioral Telemetry** (`extension/`) are **IMPLEMENTED** (with Phase 4 pending manual verification in Google Chrome). The extension captures cursor movement dynamics, extracts 10 privacy-preserving kinematic features, bounds coordinates to short-lived in-memory buffers (cleared upon extraction), and validates envelopes at the service worker gateway. **Keyboard telemetry, login detection, backend API, ML risk scoring, and dashboard remain PLANNED.**

---

## Implemented Extension Scaffold (Phase 1)

Member 1 has delivered and manually verified the foundational Manifest V3 browser extension under `extension/` and test harness under `test-page/`:

- **Manifest V3 (`extension/manifest.json`)**: Configured with minimal permissions and scoped strictly to local development hosts (`http://localhost/*`, `http://127.0.0.1/*`).
- **Background Service Worker (`extension/background/service-worker.js`)**: Manages extension lifecycle and registers installation listeners without network calls.
- **Content Script (`extension/content/content.js`)**: Verified injection point into target login pages; purely logs execution in DevTools.
- **Popup UI (`extension/popup/`)**: Self-contained UI with SentinelGuard branding, an Active status badge, and an interactive ON/OFF toggle switch.
- **Local Test Environment (`test-page/`)**: Minimal static HTML page used to verify content script injection on `http://localhost:3000/`.
- **Manual Verification Summary (Google Chrome)**:
  - Extension loads in unpacked Developer Mode: **PASS**
  - Popup opens & toggle functions interactively: **PASS**
  - Service worker initializes (`[SentinelGuard] Service worker initialized.`): **PASS**
  - Content script injection on `http://localhost:3000/` (`[SentinelGuard] Content script loaded.`): **PASS**
  - Network isolation (0 outbound telemetry/API calls): **PASS**
- **Privacy & Safety Invariant**: In this phase, zero keystrokes, mouse positions, form inputs, passwords, or credentials are captured or transmitted. All behavioral capture, batching, and backend communication remain PLANNED.

---

## Implemented Runtime Messaging Pipeline (Phase 2)

Member 1 has delivered and manually verified one-way internal runtime messaging from `content.js` to `service-worker.js`:

- **One-Way IPC Channel**: `chrome.runtime.sendMessage()` dispatches a minimal, safe `{ type: "TEST_EVENT", timestamp: Date.now() }` payload upon content script load.
- **Service Worker Validation**: `chrome.runtime.onMessage` listener strictly validates `TEST_EVENT`, logs receipt, and logs the preserved timestamp without permanent storage or network egress.
- **Manual Verification Summary (Google Chrome)**:
  - Webpage Console (`http://localhost:3000/`): Logs `[SentinelGuard] Content script loaded.` and `[SentinelGuard] Test event sent.`: **PASS**
  - Service Worker Console: Logs `[SentinelGuard] Service worker initialized.`, `[SentinelGuard] Test event received.`, and timestamp `1789020905477`: **PASS**
  - Payload integrity: Timestamp transferred intact without serialization errors: **PASS**
  - Network isolation: Zero outbound network/telemetry requests: **PASS**
- **Safety Invariant**: No mouse tracking, keystroke dynamics, login interaction detection, event buffering, or backend API integration implemented. All behavioral signal capture remains strictly PLANNED.

---

## Implemented Session & Event Identity Foundation (Phase 3)

Member 1 has delivered and manually verified the session and event identity pipeline (`extension/utils/identity.js`):

- **Centralized Identity Module**: Shared `SentinelIdentity` module provides a single source of truth for cryptographic UUID v4 identifier generation (`generateSessionId()`, `generateEventId()`), envelope assembly (`createEventEnvelope()`), and gateway schema validation (`validateEventEnvelope()`).
- **Opaque Session Scoping**: Session IDs (`sess_<uuid-v4>`) are held in content script private memory per page observation lifecycle. Multiple tabs and page reloads maintain completely isolated, unlinked session contexts. Zero PII, device IDs, or cookies used.
- **Unique Event Identity**: Every telemetry event receives an immutable `event_id` (`evt_<uuid-v4>`) and positive integer timestamp.
- **Service Worker Gateway Validation**: The background service worker validates the envelope structure against strict type/format rules before acknowledging or logging.
- **Manual Verification Summary (Google Chrome)**:
  - Initial Page Load: Service worker received and validated `TEST_EVENT` with unique `session_id`, `event_id`, and valid timestamp: **PASS**
  - Page Reload (`F5`): Service worker confirmed second `TEST_EVENT` with rolled-over, distinct `session_id` and fresh `event_id`: **PASS**
  - Session lifecycle: Proved clean session rollover without persistent state or cross-session leakage: **PASS**
  - Network isolation: Zero outbound network/telemetry calls: **PASS**
- **Safety Invariant**: No mouse coordinates, keystroke timings, login detection, event buffering, or backend API transmission implemented. All behavioral signal capture remains strictly PLANNED.

---

## Implemented Mouse Behavioral Telemetry (Phase 4 — Pending Manual Verification)

Member 1 has delivered the first behavioral signal collection layer (`extension/utils/mouse-features.js`, `extension/content/content.js`, `extension/background/service-worker.js`):

- **Passive Throttled Sampling**: Mouse movements sampled at 50 ms intervals (~20 Hz engineering trade-off balancing human motor dynamics against CPU overhead).
- **Ephemeral Bounded Buffering**: In-memory buffer capped at 25 points (~1.25s continuous movement) with a 500 ms idle debounce timer.
- **Client-Side Behavioral Feature Extraction**: Computes 10 privacy-preserving kinematic features (`movement_count`, `total_distance`, `average_velocity`, `maximum_velocity`, `velocity_variance`, `direction_change_count`, `average_direction_change`, `path_efficiency`, `straightness_ratio`, `movement_duration`).
- **Coordinate Privacy**: Raw coordinates exist only temporarily in memory during sampling and are immediately purged after feature extraction. Zero raw coordinates are persisted, logged, or sent over IPC.
- **Envelope Integration**: Reuses Phase 3 `SentinelIdentity.createEventEnvelope()` with `currentSessionId` and `eventType: "MOUSE_BEHAVIOR"`.
- **Protection State Synchronization**: Extension popup toggle synchronizes with `chrome.storage.local`. When protection is toggled OFF, sampling immediately ceases, buffers are cleared, and pending telemetry is suppressed.
- **Service Worker Validation Gateway**: Background worker validates envelope structure and enforces finite numerical boundaries on all 10 feature values.
- **Safety Invariant**: Zero keyboard/keystroke capture, zero login form detection, zero DOM scraping, zero network/backend transmission.

---

## Repository Structure

```
SentinelGuard-/
├── extension/           ← [IMPLEMENTED] Member 1: Chrome browser extension
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
│       ├── identity.js        ← [IMPLEMENTED - Phase 3] Session & event ID generation & envelope validation
│       └── mouse-features.js  ← [IMPLEMENTED - Phase 4] Mathematical feature extraction & payload validation
├── backend/             ← [PLANNED] Member 2: Django REST API + ML model
├── security/            ← [PLANNED] Member 3: Adaptive security + OTP
├── dashboard/           ← [PLANNED] Member 4: Admin dashboard + demo page
├── docs/                ← [IMPLEMENTED] Project-wide documentation (all members)
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── DATA_SCHEMA.md
│   ├── PRIVACY.md
│   └── reports/
│       ├── PHASE-00-INSPECTION.md
│       ├── PHASE-01-EXTENSION-SCAFFOLDING.md
│       ├── PHASE-02-MESSAGING.md
│       └── PHASE-03-SESSION-IDENTITY.md
├── test-page/           ← [TEST HARNESS] Minimal static page for Phase 1 content-script verification
│   └── index.html
├── .gitignore
└── README.md            ← This file
```

---

## Planned High-Level Architecture

```
User (browser)
     │
     ▼
Demo / Login Page
     │
     ▼
SentinelGuard Browser Extension  ← Member 1
     │  (behavioral signals)
     ▼
Django REST API                  ← Member 2
     │
     ▼
ML Risk Scoring Engine           ← Member 2
     │  (risk score)
     ▼
Adaptive Security Layer          ← Member 3
     │  (allow / challenge / block)
     ▼
OTP / Step-Up Challenge          ← Member 3
     │
     ▼
Admin Dashboard                  ← Member 4
```

---

## Documentation

All project documentation lives in [`docs/`](./docs/README.md).

| Document | Purpose |
|----------|---------|
| [`docs/README.md`](./docs/README.md) | Documentation index and navigation guide |
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | System architecture (Scaffold IMPLEMENTED; Capture PLANNED) |
| [`docs/DATA_SCHEMA.md`](./docs/DATA_SCHEMA.md) | Behavioral event schema (provisional) |
| [`docs/PRIVACY.md`](./docs/PRIVACY.md) | Privacy-by-design principles |
| [`docs/reports/PHASE-00-INSPECTION.md`](./docs/reports/PHASE-00-INSPECTION.md) | Phase 0 inspection report |
| [`docs/reports/PHASE-01-EXTENSION-SCAFFOLDING.md`](./docs/reports/PHASE-01-EXTENSION-SCAFFOLDING.md) | Phase 1 extension scaffolding report |
| [`docs/reports/PHASE-02-MESSAGING.md`](./docs/reports/PHASE-02-MESSAGING.md) | Phase 2 runtime messaging verification report |
| [`docs/reports/PHASE-03-SESSION-IDENTITY.md`](./docs/reports/PHASE-03-SESSION-IDENTITY.md) | Phase 3 session & event identity report |

---

## Branch Strategy (PLANNED — Team Agreement Required)

```
main                     ← stable, reviewed code only
feature/member1-extension
feature/member2-backend
feature/member3-security
feature/member4-dashboard
```

All feature branches merge into `main` via pull requests with at least one reviewer.

---

## Privacy Commitment

SentinelGuard is designed with **privacy by default**:

- **No passwords or credentials are ever captured.**
- Only behavioral *metadata* (timing, rhythm, interaction patterns) is transmitted — never content.
- The extension provides an explicit **ON/OFF control** for full user transparency.

See [`docs/PRIVACY.md`](./docs/PRIVACY.md) for full details.

---

*SentinelGuard — Defending login integrity through behavioral intelligence.*
