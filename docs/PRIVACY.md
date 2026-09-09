# SentinelGuard — Privacy by Design

> **STATUS: BINDING DESIGN COMMITMENT**
> This document is not a guideline — it is a constraint.
> Member 1's browser extension implementation MUST comply with every principle in this document.
> Violations of these principles are bugs, not design choices.

---

## Guiding Principle

SentinelGuard operates at the boundary between security and privacy. We collect behavioral metadata to protect users from credential-stuffing attacks, but we do so in a way that treats user privacy as a non-negotiable constraint, not a trade-off.

**Privacy is not balanced against security in SentinelGuard. Both are requirements.**

---

## What the Extension WILL Collect

The following behavioral metadata is permitted to be captured and transmitted to the backend:

### 1. Anonymous Session Identifier
- A randomly generated, non-guessable session token (e.g., UUIDv4) created per login interaction.
- Must NOT be linked to the user's account, email, or identity.
- Must NOT persist across browser sessions (ephemeral only).

### 2. Timestamps and Timing Metadata
- Event timestamps in milliseconds (e.g., when a key was pressed down, when it was released).
- Inter-event timing deltas (e.g., time between consecutive keystrokes).
- Duration of specific actions (e.g., how long the user held a key, time from first field focus to form submit).
- **Collected:** The *when* and *how long*.
- **Not collected:** The *what* (which key was pressed, what was typed).

### 3. Mouse Movement Metadata
- (x, y) coordinates of mouse movement events, sampled at a reasonable interval.
- Mouse velocity (derived from position + timestamp pairs).
- Click position (x, y) and click event timestamps.
- Mouse entry/exit events relative to form fields.
- **Collected:** Cursor trajectory and click mechanics.
- **Not collected:** What UI element was hovered over (no element labels or IDs that could reveal page structure beyond the login form scope).

### 4. Typing Rhythm / Keystroke Dynamics
- `keydown` and `keyup` timestamps for each keystroke event.
- Flight time (time between one key's `keyup` and the next key's `keydown`).
- Dwell time (time between `keydown` and `keyup` for a single key).
- **Collected:** Timing metadata only — the rhythm of typing.
- **Not collected:** The `event.key` value, the `event.code` value, or any data that identifies which key was pressed.

### 5. Login Form Interaction Metadata
- Focus and blur events on form fields (with field type: username vs. password field, not field content).
- Number of backspace/delete events (as a count, not revealing what was corrected).
- Form submission event (timestamp only).
- Copy/paste event occurrence (as a boolean flag: did a paste event occur in the password field?).
- **Collected:** Interaction patterns — how the user engaged with the form mechanically.
- **Not collected:** Field content, partial field content, or any data that could reconstruct what was typed.

---

## What the Extension Will NEVER Collect

The following are explicitly prohibited. These are **hard limits**, not soft guidelines.

### ❌ Passwords and Credentials
- The value of any password field.
- Any partial characters from a password field.
- The value of any username, email, or account identifier field.
- Any data that could be used to reconstruct a credential.

### ❌ Raw Key Values
- `event.key` — the character that was typed.
- `event.code` — the physical key code.
- Any sequence of key values that could reconstruct typed text.
- Even in non-password fields, key values are never transmitted.

### ❌ Clipboard Contents
- The content of any clipboard paste event.
- The result of any `navigator.clipboard.readText()` or equivalent call.
- The paste event itself may be recorded as a boolean flag (did a paste occur?), but never the pasted content.

### ❌ Unnecessary Page Content
- DOM content, innerHTML, textContent of any element.
- Form field values or placeholder text.
- Page title, URL beyond the domain (no path or query parameters).
- Any data identifying the user beyond the ephemeral session token.

### ❌ Persistent Identifiers
- No browser fingerprinting.
- No reading of cookies.
- No access to `localStorage` or `sessionStorage` of the target page.
- No tracking across pages or sessions.

---

## Why Typing Rhythm Can Be Collected Without Storing Characters

This is a foundational design decision and a common question.

**Keystroke dynamics** is the study of the *timing pattern* of how someone types, independent of what they type. It is analogous to a handwriting analysis that looks at pen pressure and stroke duration rather than the letters formed.

The key insight is:

> A genuine human typing a 10-character password generates a sequence of 10 `keydown`→`keyup` pairs with specific dwell times and flight times between them. A bot auto-filling the same field generates a pattern that is measurably different — typically either instantaneous or with artificially regular timing.

SentinelGuard captures only the **timing vector** — an array of numbers (milliseconds) representing dwell and flight times. This vector:
- Contains **no character information whatsoever**.
- Cannot be reversed to reconstruct the typed text.
- Is mathematically sufficient to distinguish bot behavior from human behavior.
- Is the minimum necessary data for the ML model's purpose.

**Example of what IS transmitted:**
```json
"keystroke_timings": [
  { "dwell_ms": 87, "flight_ms": 112 },
  { "dwell_ms": 94, "flight_ms": 78 },
  { "dwell_ms": 103, "flight_ms": 130 }
]
```

**Example of what is NEVER transmitted:**
```json
// PROHIBITED — this would reveal the typed character
"keystroke_timings": [
  { "key": "p", "dwell_ms": 87 },
  ...
]
```

The field name `key` is never present. The `event.key` value is read only to determine *whether* to ignore a modifier key (e.g., Shift, Ctrl), and is immediately discarded — never stored, buffered, or transmitted.

---

## User Transparency and Control

### ON/OFF Toggle (PLANNED — Member 1 Implementation Requirement)

The SentinelGuard extension must provide a clearly visible toggle in its popup UI that allows the user to:

- **Disable** all signal capture with a single click.
- **Re-enable** signal capture with a single click.
- **See the current status** of signal capture (active indicator in the extension badge/icon).

When the extension is disabled:
- No event listeners are attached to the page.
- No data is buffered.
- No API calls are made.
- The extension is completely passive.

This toggle is a **non-negotiable requirement**, not a nice-to-have feature. User control over data collection is a fundamental privacy right.

### Extension Badge States (PLANNED)

| Badge | Meaning |
|-------|---------|
| 🟢 Green / "ON" | Extension is active and capturing signals |
| ⚫ Grey / "OFF" | Extension is disabled by user; no capture occurring |

---

## Data Minimization Principle

Member 1 must apply data minimization at every design decision:

> **If a signal is not directly needed by the ML model for bot detection, it must not be collected.**

Before adding any new field to the event payload, Member 1 must ask:
1. Does Member 2's ML model actually need this field?
2. Is there a less privacy-invasive way to achieve the same detection goal?
3. Can this field be further abstracted (e.g., a count instead of a list)?

If the answer to question 1 is "not sure", the field must not be added until confirmed with Member 2.

---

## Regulatory Context (Informational)

The following privacy regulations are relevant context for SentinelGuard's design, though this project is an academic prototype:

| Regulation | Key Principle Relevant to SentinelGuard |
|---|---|
| GDPR (EU) | Purpose limitation, data minimization, right to opt out |
| CCPA (California) | Right to know what is collected, right to opt out of sale/sharing |
| PIPEDA (Canada) | Consent, limiting collection to necessary data |

Even as an academic project, SentinelGuard's design should be defensible against these standards. The privacy principles in this document are sufficient for compliance if the implementation follows them faithfully.

---

## Violations and Consequences

If any committed code violates the "NEVER Collect" principles above, it must be treated as a **blocking bug** that must be fixed before the code is merged into `main`. No exception.

Specifically:
- Any code that reads `event.key` or `event.code` and stores or transmits the value is a **critical privacy violation**.
- Any code that reads a password field's `.value` property is a **critical privacy violation**.
- Any code that transmits clipboard content is a **critical privacy violation**.

---

*Last updated: Phase 0 — Documentation Foundation*
*Maintained by: Member 1*
*Reviewed by: All members (required before Phase 1 implementation begins)*
