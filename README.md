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
PHASE 2 — PENDING    ⏳  Django backend + ML model (Member 2)
PHASE 3 — PENDING    ⏳  Adaptive security + OTP (Member 3)
PHASE 4 — PENDING    ⏳  Admin dashboard + demo page (Member 4)
PHASE 5 — PENDING    ⏳  Integration & end-to-end testing (all members)
```

> **Current Implementation Note:** The Chrome Manifest V3 browser extension scaffold (`extension/`) is **IMPLEMENTED**. It initializes the service worker, content script, and popup UI. **Behavioral signal capture (mouse, keystrokes, form telemetry) is NOT implemented yet** and remains PLANNED. All backend, ML, security, and dashboard components are PLANNED.

---

## Implemented Extension Scaffold (Phase 1)

Member 1 has delivered the foundational Manifest V3 browser extension under `extension/`:

- **Manifest V3 (`extension/manifest.json`)**: Configured with minimal permissions and scoped strictly to local development hosts (`http://localhost/*`, `http://127.0.0.1/*`).
- **Background Service Worker (`extension/background/service-worker.js`)**: Manages extension lifecycle and registers installation listeners without network calls.
- **Content Script (`extension/content/content.js`)**: Verified injection point into target login pages; purely logs execution in DevTools.
- **Popup UI (`extension/popup/`)**: Self-contained UI with SentinelGuard branding, an Active status badge, and an interactive ON/OFF toggle switch.
- **Privacy & Safety Invariant**: In this phase, zero keystrokes, mouse positions, form inputs, passwords, or credentials are captured or transmitted.

---

## Repository Structure

```
SentinelGuard-/
├── extension/           ← [IMPLEMENTED - Scaffold] Member 1: Chrome browser extension
│   ├── manifest.json
│   ├── background/
│   │   └── service-worker.js
│   ├── content/
│   │   └── content.js
│   └── popup/
│       ├── popup.html
│       ├── popup.css
│       └── popup.js
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
│       └── PHASE-01-EXTENSION-SCAFFOLDING.md
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
