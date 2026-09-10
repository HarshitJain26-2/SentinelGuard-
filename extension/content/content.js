/**
 * SentinelGuard — Content Script
 * 
 * Phase 3 Scope:
 * - Session and event identity initialization using SentinelIdentity utility.
 * - Dispatches a structured TEST_EVENT envelope over runtime messaging.
 * 
 * Safety & Privacy Notice:
 * - NO mouse movement tracking
 * - NO keystroke or typing timing tracking
 * - NO form value, password, or credential access
 * - NO DOM reading or scraping
 * - NO network or API transmission
 */

console.log("[SentinelGuard] Content script loaded.");

// Generate an isolated, opaque session ID for this page observation lifecycle
const currentSessionId = (typeof SentinelIdentity !== "undefined")
  ? SentinelIdentity.generateSessionId()
  : ("sess_" + crypto.randomUUID());

// Construct a structured development test event envelope
const testPayload = (typeof SentinelIdentity !== "undefined")
  ? SentinelIdentity.createEventEnvelope({
      sessionId: currentSessionId,
      eventType: "TEST_EVENT"
    })
  : {
      type: "TEST_EVENT",
      event_type: "TEST_EVENT",
      event_id: "evt_" + crypto.randomUUID(),
      session_id: currentSessionId,
      timestamp: Date.now()
    };

chrome.runtime.sendMessage(testPayload, () => {
  if (chrome.runtime.lastError) {
    // Suppress or handle if background worker is spinning up
  }
});

console.log("[SentinelGuard] Test event sent.");
