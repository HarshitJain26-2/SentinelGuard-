# SentinelGuard — Documentation Index

This folder contains all project-wide documentation for **SentinelGuard: AI-Driven Bot & Credential-Stuffing Defense System**.

---

## Documentation Philosophy

All documentation in this project follows three strict labels to distinguish what is real from what is intended:

| Label | Meaning |
|-------|---------|
| **IMPLEMENTED** | Code or functionality that actually exists in this repository and has been committed. |
| **PLANNED** | Something the team intends to implement in a future phase. Not yet written. |
| **PROVISIONAL** | A proposal or draft that has been written down but is not yet agreed upon by all relevant members. Requires explicit sign-off before being treated as binding. |

> **Rule:** Never document a component as IMPLEMENTED unless the code is committed and verifiable. Aspirational descriptions must always be labeled PLANNED or PROVISIONAL.

---

## What This Folder Contains

```
docs/
├── README.md              ← This file. Documentation index and navigation guide.
├── ARCHITECTURE.md        ← Planned system architecture. All four members' components.
├── DATA_SCHEMA.md         ← Provisional behavioral event schema. Requires Member 2 sign-off.
├── PRIVACY.md             ← Privacy-by-design principles. Binding commitment for Member 1.
└── reports/
    └── PHASE-00-INSPECTION.md  ← Permanent Phase 0 inspection report.
```

---

## Document Summaries

### [`ARCHITECTURE.md`](./ARCHITECTURE.md)
Describes the overall planned system architecture for SentinelGuard. Covers all four members' components, their boundaries, and how data flows between them. This is the single authoritative reference for understanding how the system fits together.

**Status: PLANNED** — No application code exists yet.

---

### [`DATA_SCHEMA.md`](./DATA_SCHEMA.md)
Defines the provisional behavioral event payload that Member 1's browser extension will send to Member 2's Django backend API. This document is the primary coordination artifact between Members 1 and 2.

**Status: PROVISIONAL** — Requires explicit agreement between Member 1 and Member 2 before integration begins.

---

### [`PRIVACY.md`](./PRIVACY.md)
Documents the privacy-by-design principles that govern what the browser extension may and may not collect. These principles are a binding constraint on Member 1's implementation, not optional guidelines.

**Status: BINDING DESIGN COMMITMENT** — Member 1 must adhere to this document during implementation.

---

### [`reports/PHASE-00-INSPECTION.md`](./reports/PHASE-00-INSPECTION.md)
The permanent phase report for Phase 0. Records the repository state at the beginning of the project, inspection findings, ownership boundaries, identified risks, and coordination requirements. Each development phase will produce a corresponding report in this folder.

**Status: COMPLETE** — Phase 0 inspection is done.

---

## Phase Reports

Each development phase produces a permanent report stored in `docs/reports/`:

| Report | Phase | Status |
|--------|-------|--------|
| [`PHASE-00-INSPECTION.md`](./reports/PHASE-00-INSPECTION.md) | Phase 0 — Repository Inspection | ✅ Complete |
| `PHASE-01-EXTENSION.md` | Phase 1 — Browser Extension Scaffold | ⏳ Pending |
| `PHASE-02-BACKEND.md` | Phase 2 — Django Backend + ML Model | ⏳ Pending |
| `PHASE-03-SECURITY.md` | Phase 3 — Adaptive Security + OTP | ⏳ Pending |
| `PHASE-04-DASHBOARD.md` | Phase 4 — Admin Dashboard | ⏳ Pending |
| `PHASE-05-INTEGRATION.md` | Phase 5 — Integration & Testing | ⏳ Pending |

---

## How to Navigate the Documentation

**If you are new to the project**, read in this order:
1. Root [`README.md`](../README.md) — project overview and team structure.
2. [`ARCHITECTURE.md`](./ARCHITECTURE.md) — how the system is designed.
3. [`PRIVACY.md`](./PRIVACY.md) — non-negotiable privacy commitments.
4. [`DATA_SCHEMA.md`](./DATA_SCHEMA.md) — event payload schema (Members 1 and 2 especially).
5. [`reports/PHASE-00-INSPECTION.md`](./reports/PHASE-00-INSPECTION.md) — where the project started.

**If you are Member 1 (Extension):**
- Your primary binding documents are [`PRIVACY.md`](./PRIVACY.md) and [`DATA_SCHEMA.md`](./DATA_SCHEMA.md).
- Your implementation lives in `extension/` (PLANNED — not yet created).
- Your documentation contributions belong in `docs/`.

**If you are Member 2 (Backend + ML):**
- Review [`DATA_SCHEMA.md`](./DATA_SCHEMA.md) and provide sign-off or propose changes before Member 1 begins API integration.

**If you are Member 3 (Security + OTP):**
- Review [`ARCHITECTURE.md`](./ARCHITECTURE.md) — your component sits between the ML risk score and the user-facing response.

**If you are Member 4 (Dashboard + Demo):**
- Review [`ARCHITECTURE.md`](./ARCHITECTURE.md) — the demo login page is the entry point that the extension observes.

---

## Member 1 — Documentation Ownership

Member 1 is responsible for maintaining the following documentation:

| Document | Member 1 Role |
|----------|---------------|
| [`DATA_SCHEMA.md`](./DATA_SCHEMA.md) | Primary author; must coordinate with Member 2 for finalization |
| [`PRIVACY.md`](./PRIVACY.md) | Primary author; binding for Member 1's own implementation |
| `docs/reports/PHASE-0X-*.md` | Contributes phase reports for phases Member 1 leads |

Member 1 does **not** own or maintain documentation describing Member 2, 3, or 4's internal implementation details. Member 1 documents only the *interface* between the extension and the backend (i.e., the API payload schema).

---

*Last updated: Phase 0 — Documentation Foundation*
