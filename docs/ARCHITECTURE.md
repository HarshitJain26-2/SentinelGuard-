# SentinelGuard — System Architecture

> **STATUS: PARTIALLY IMPLEMENTED (Phases 1, 2 & 3 Complete — Manually Verified)**
> This document describes the architecture of SentinelGuard.
> **Implemented components:** Manifest V3 extension scaffold (`extension/manifest.json`), content script scaffold (`extension/content/content.js`), background service worker scaffold (`extension/background/service-worker.js`), popup UI (`extension/popup/`), local test page / verification environment (`test-page/index.html`), Content Script ↔ Service Worker runtime messaging, Session Identity, Event Identity, and Event Envelope (`extension/utils/identity.js`).
> **Planned components:** Behavioral signal capture, mouse telemetry, typing rhythm telemetry, login interaction detection, event batching, backend API transmission, Django backend, ML model, adaptive security & OTP, admin dashboard.
> All components not explicitly marked IMPLEMENTED remain PLANNED.

---

## Overview

SentinelGuard is a distributed, four-component system designed to detect and mitigate bot-driven credential-stuffing attacks at login forms. Detection is based on **behavioral biometrics** — the unique physical interaction patterns of real human users — rather than network-layer signals alone.

---

## Component Owners

| Component | Member | Status |
|-----------|--------|--------|
| Browser Extension (Scaffold, Messaging, Identity) | **Member 1** | **IMPLEMENTED (Phases 1, 2 & 3)** |
| Local Test Page / Verification Environment | **Member 1** | **IMPLEMENTED** |
| Behavioral Signal Capture | **Member 1** | PLANNED |
| Django Backend + ML Risk Model | **Member 2** | PLANNED |
| Adaptive Security Logic + OTP | **Member 3** | PLANNED |
| Admin Dashboard + Demo Login Page | **Member 4** | PLANNED |

---

## High-Level System Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        USER (Browser)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │  navigates to
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Demo / Login Page    [Member 4]                 │
│        (HTML login form — target of extension observation)  │
└─────────────────────────┬───────────────────────────────────┘
                          │  extension injects content script
                          ▼
┌─────────────────────────────────────────────────────────────┐
│       SentinelGuard Browser Extension   [Member 1]          │
│                                                             │
│  ┌─────────────────┐   ┌──────────────────┐                │
│  │  Content Script │   │ Background Service│                │
│  │                 │   │     Worker        │                │
│  │ • Mouse events  │──▶│ • Event buffer   │                │
│  │ • Key timing    │   │ • Batch flush    │                │
│  │ • Form events   │   │ • HTTP POST      │                │
│  └─────────────────┘   └────────┬─────────┘                │
│                                 │                           │
│  ┌─────────────────┐            │                           │
│  │  Popup UI       │            │                           │
│  │ • ON/OFF toggle │            │                           │
│  │ • Status badge  │            │                           │
│  └─────────────────┘            │                           │
└────────────────────────────────-┼───────────────────────────┘
                                  │ HTTPS POST /api/v1/events/
                                  ▼ (Behavioral event payload)
┌─────────────────────────────────────────────────────────────┐
│              Django REST API    [Member 2]                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Feature Engineering Layer                │   │
│  │  • Parse behavioral event payload                   │   │
│  │  • Compute derived features (inter-keystroke timing,│   │
│  │    mouse velocity, click-to-submit duration, etc.)  │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │               ML Risk Scoring Engine                │   │
│  │  • Trained classification model                     │   │
│  │  • Outputs: risk_score (0.0 – 1.0), label           │   │
│  └────────────────────────┬────────────────────────────┘   │
└────────────────────────────┼────────────────────────────────┘
                             │ risk_score + session_id
                             ▼
┌─────────────────────────────────────────────────────────────┐
│         Adaptive Security Layer    [Member 3]                │
│                                                             │
│  if risk_score < LOW_THRESHOLD  → allow login               │
│  if risk_score < HIGH_THRESHOLD → step-up OTP challenge     │
│  if risk_score ≥ HIGH_THRESHOLD → soft block / flag         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                OTP / Challenge System               │   │
│  │  • Email or TOTP second-factor                      │   │
│  │  • Challenge delivery + verification                │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │ session decisions + risk events
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Admin Dashboard    [Member 4]                   │
│                                                             │
│  • Real-time risk event feed                                │
│  • Session log with risk scores                             │
│  • Threshold configuration UI                               │
│  • Blocked / challenged session management                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Detail

### Member 1 — Browser Extension [IMPLEMENTED: Scaffold; PLANNED: Signal Capture]

**Repository path:** `extension/` (**IMPLEMENTED**)

**Purpose:** Capture behavioral signals from the user's interaction with a login form and transmit them securely to the backend for risk analysis.

**Scaffold and Sub-components:**

| Sub-component | File / Path | Status | Responsibility |
|---------------|-------------|--------|----------------|
| Manifest V3 Extension Scaffold | `extension/manifest.json` | **IMPLEMENTED** | Chrome Manifest V3 descriptor |
| Content Script Scaffold | `extension/content/content.js` | **IMPLEMENTED** | Injected into target pages; verified loading on localhost |
| Background Service Worker Scaffold | `extension/background/service-worker.js` | **IMPLEMENTED** | Background service worker; initializes lifecycle |
| Popup UI | `extension/popup/popup.html`, `popup.css`, `popup.js` | **IMPLEMENTED** | Displays ON/OFF toggle UI and status badge |
| Local Test Page / Verification Environment | `test-page/index.html` | **IMPLEMENTED** | Minimal static page to verify localhost:3000 injection |
| Behavioral Signal Capture | Content script listeners | PLANNED | Observes user interaction on login form |
| Mouse Telemetry | Content script mouse listener | PLANNED | Captures cursor movement coordinates & velocity |
| Typing Rhythm Telemetry | Content script keyboard listener | PLANNED | Measures dwell/flight timing (no key values) |
| Login Interaction Detection | Content script form hooks | PLANNED | Detects interaction with login fields |
| Content Script ↔ Service Worker Event Messaging | Extension runtime messaging | **IMPLEMENTED — PHASE 2** | Passes runtime messages from content script to service worker |
| Session Identity | `extension/utils/identity.js` | **IMPLEMENTED — PHASE 3 (Manually Verified)** | Generates opaque, cryptographically random session IDs (`sess_<uuid>`) |
| Event Identity | `extension/utils/identity.js` | **IMPLEMENTED — PHASE 3 (Manually Verified)** | Generates unique UUID v4 event IDs (`evt_<uuid>`) for all telemetry events |
| Event Envelope | `extension/utils/identity.js` | **IMPLEMENTED — PHASE 3 (Manually Verified)** | Standardized envelope schema and validation for IPC events |
| Event Batching | `extension/utils/signal_buffer.js` (planned) | PLANNED | Buffers and batches captured events |
| Backend API Transmission | Service worker fetch/POST | PLANNED | Sends batched events to Django backend API |

**Signals captured (PLANNED — subject to privacy constraints in [`PRIVACY.md`](./PRIVACY.md)):**

- Mouse movement coordinates and timing (PLANNED)
- Typing inter-keystroke timing (NOT key values or characters) (PLANNED)
- Click events and timing (PLANNED)
- Form field focus/blur events (PLANNED)
- Login form submission event (PLANNED)

**Signals never captured:**

- Password characters or values
- Any text typed into input fields
- Clipboard contents

**API boundary:** Member 1 sends a single HTTP POST per session to an endpoint provided by Member 2. The payload schema is defined in [`DATA_SCHEMA.md`](./DATA_SCHEMA.md) (PROVISIONAL). Behavioral signal transmission is **PLANNED** for a later phase.

---

### Member 2 — Django Backend + ML Model (PLANNED)

**Repository path:** `backend/` (PLANNED — does not exist yet)

**Purpose:** Receive behavioral event payloads, extract features, run the ML risk model, and return or store a risk score.

**Planned components:**
- Django REST Framework API (`/api/v1/events/` endpoint)
- Feature engineering pipeline
- ML classification model (bot vs. human)
- Database (session log, risk scores)

**API contract with Member 1:** Must be agreed and written into [`DATA_SCHEMA.md`](./DATA_SCHEMA.md) before integration begins.

---

### Member 3 — Adaptive Security + OTP (PLANNED)

**Repository path:** `security/` (PLANNED — does not exist yet)

**Purpose:** Consume risk scores from the ML model and apply proportional security responses.

**Planned components:**
- Threshold-based decision engine (configurable LOW / HIGH thresholds)
- OTP challenge delivery (email or TOTP)
- OTP verification endpoint
- Session flagging / blocking logic

---

### Member 4 — Admin Dashboard + Demo Login Page (PLANNED)

**Repository path:** `dashboard/` (PLANNED — does not exist yet)

**Purpose:**
1. Provide a demo login page that the browser extension observes (integration target).
2. Provide an admin UI for monitoring risk events, sessions, and thresholds.

**Planned components:**
- Demo HTML login form
- Admin dashboard (charts, session feed, risk event log)
- Threshold configuration controls

---

## Inter-Component Data Flows

```
 Member 1 → Member 2 : Behavioral event payload (HTTP POST, JSON)
 Member 2 → Member 3 : Risk score + session_id (internal Django call or REST)
 Member 3 → Member 4 : Session decisions + risk events (DB read / API)
 Member 4 → User     : OTP challenge UI + admin dashboard UI
 Member 4 → Member 1 : Demo login page (target for content script injection)
```

---

## Security Architecture Principles (PLANNED)

- All communication between extension and backend over **HTTPS only**.
- Extension uses `chrome.storage.session` (not `localStorage`) for ephemeral session state.
- No credentials, passwords, or raw typed content ever leave the browser.
- Backend API authenticates extension requests (mechanism TBD — Member 2 to specify).
- Behavioral data is treated as sensitive; storage and retention policy TBD (Member 2 + Member 3).

---

## Technology Stack
| Layer | Technology | Member | Status |
|-------|-----------|--------|--------|
| Browser Extension | Chrome Manifest V3, Vanilla JS | Member 1 | **IMPLEMENTED (Scaffold)** |
| Backend API | Python, Django, Django REST Framework | Member 2 | PLANNED |
| ML Model | scikit-learn / PyTorch (TBD) | Member 2 | PLANNED |
| Security Logic | Django middleware / signals | Member 3 | PLANNED |
| OTP | TOTP library / email backend (TBD) | Member 3 | PLANNED |
| Admin Dashboard | React or Vanilla JS + Chart.js (TBD) | Member 4 | PLANNED |
| Database | PostgreSQL or SQLite (dev) | Member 2 | PLANNED |

---

## Open Architecture Questions (Require Team Agreement)

| # | Question | Blocking For |
|---|----------|-------------|
| 1 | What is the exact Django API endpoint URL and auth mechanism? | Member 1 integration |
| 2 | Does Member 2 return a risk score synchronously or asynchronously? | Member 3 design |
| 3 | What is the session identifier scheme? (UUID? server-assigned? extension-assigned?) | Members 1, 2, 3 |
| 4 | What are the LOW and HIGH risk thresholds? | Member 3 |
| 5 | Is the OTP challenge delivered inline (same page) or via redirect? | Members 3, 4 |
| 6 | What database is used for production? | Member 2 |
| 7 | Branch strategy and PR review assignment | All members |

---

*Last updated: Phase 1 — Browser Extension Scaffold*
*All components not explicitly marked IMPLEMENTED remain PLANNED.*
