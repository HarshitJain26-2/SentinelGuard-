/**
 * SentinelGuard — Background Service Worker
 * 
 * Phase 3 Scope:
 * - Listens for structured runtime event messages from the content script.
 * - Validates session_id, event_id, event_type, and timestamp using SentinelIdentity.
 * - Logs validated identity metadata.
 * 
 * Safety & Privacy Notice:
 * - NO API requests or network calls
 * - NO event collection or buffering
 * - NO permanent storage persistence
 * - NO machine learning integration
 * - NO authentication logic
 */

importScripts("../utils/identity.js");

console.log("[SentinelGuard] Service worker initialized.");

chrome.runtime.onInstalled.addListener(() => {
  console.log("[SentinelGuard] Extension installed successfully.");
});

// Phase 3: Listen for structured events from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || typeof message !== "object") {
    return;
  }

  const eventType = message.event_type || message.type;
  if (eventType === "TEST_EVENT") {
    // Validate identity envelope structure
    const validation = (typeof SentinelIdentity !== "undefined")
      ? SentinelIdentity.validateEventEnvelope(message)
      : { valid: Boolean(message.event_id && message.session_id && message.timestamp) };

    if (!validation.valid) {
      console.warn("[SentinelGuard] Rejected invalid event envelope:", validation.errors);
      if (sendResponse) {
        sendResponse({ status: "REJECTED", errors: validation.errors });
      }
      return;
    }

    console.log("[SentinelGuard] Event received.");
    console.log("[SentinelGuard] session_id:", message.session_id);
    console.log("[SentinelGuard] event_id:", message.event_id);
    console.log("[SentinelGuard] timestamp:", message.timestamp);

    if (sendResponse) {
      sendResponse({ status: "ACK" });
    }
  }
});
