# SentinelGuard

**AI-Driven Bot & Credential-Stuffing Defense System**

SentinelGuard is a behavioral-security tool that detects bots and credential-stuffing attempts by analyzing *how* a user interacts — mouse movement, typing rhythm, and login patterns — rather than relying on static CAPTCHAs or rate limits. It applies adaptive security (stepping up to OTP only when a session looks suspicious) and gives security teams a live dashboard of threats across the organization.

## Problem Statement

Websites and apps are increasingly attacked by bots and credential-stuffing tools that mimic human behavior closely enough to defeat traditional CAPTCHAs and rate-limiting. These defenses are either too easy for sophisticated bots to bypass, or too intrusive for legitimate users.

## Solution

SentinelGuard is deployed as a **browser extension installed by admins/employees for org-wide monitoring**. It captures behavioral signals during login and general browsing, scores each session for bot-likelihood in real time using an ML model, and triggers adaptive responses:

- **Low risk** → allow silently, no friction
- **Medium risk** → step-up challenge (OTP)
- **High risk** → flag or block, alert admin

All decisions and signals feed a live admin dashboard for visibility and investigation.

## Architecture

```
SentinelGuard/
├── extension/    # Manifest V3 browser extension — captures behavioral signals
├── backend/      # API + ML detection model — scores sessions, enforces adaptive rules
├── dashboard/    # Admin web dashboard — live threat monitoring
└── docs/         # Architecture notes, write-ups, diagrams
```

### Components

1. **Extension (Client-Side Sensor)**
   Captures mouse movement (velocity, curvature, pauses), keystroke timing (dwell/flight time), and login-form interaction patterns. Runs transparently on employee devices with a visible on/off indicator.

2. **Backend (Detection Engine)**
   Receives batched behavioral events, extracts features per session, and scores each login attempt with a trained classifier (starting with Logistic Regression / Random Forest, extendable to sequence models like LSTM/1D-CNN on raw time-series signals).

3. **Adaptive Security Layer**
   Converts the risk score into action — silent allow, OTP step-up, or block — instead of applying the same challenge to every user.

4. **Dashboard (Admin Visibility)**
   Live feed of risk scores, flagged sessions, and trends across the organization, with drill-down into the specific signals behind each flag.

## Tech Stack

- **Extension:** JavaScript, Manifest V3 (content script + background service worker)
- **Backend:** Python (Django/Flask) or Node.js — TBD
- **ML:** scikit-learn baseline, with room to extend to deep learning on sequential signals
- **Dashboard:** React (or framework TBD)

## Status

🚧 In development — semester project.

## Roadmap

- [ ] Phase 1 — Extension & signal capture
- [ ] Phase 2 — Backend & detection model
- [ ] Phase 3 — Adaptive response logic
- [ ] Phase 4 — Admin dashboard & demo

## Author

**Mayuri** — [github.com/MMTapkire31](https://github.com/MMTapkire31)