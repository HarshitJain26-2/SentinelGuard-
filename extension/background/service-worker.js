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
importScripts("../utils/mouse-features.js");

console.log("[SentinelGuard] Service worker initialized.");

chrome.runtime.onInstalled.addListener(() => {
  console.log("[SentinelGuard] Extension installed successfully.");
});

let isProtectionEnabled = true;

if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
  chrome.storage.local.get(["protectionEnabled"], (result) => {
    if (!chrome.runtime.lastError && result && "protectionEnabled" in result) {
      isProtectionEnabled = result.protectionEnabled !== false;
    }
    console.log("[SentinelGuard][DEBUG] Initial SW protection state:", isProtectionEnabled);
  });

  chrome.storage.onChanged.addListener((changes) => {
    if (changes && "protectionEnabled" in changes) {
      const oldVal = changes.protectionEnabled.oldValue;
      const newVal = changes.protectionEnabled.newValue;
      isProtectionEnabled = newVal !== false;
      console.log(`[SentinelGuard][DEBUG] SW protection changed: ${oldVal} -> ${newVal}`);
    }
  });
}

function processMouseBehavior(message, sendResponse) {
  // 1. Validate envelope identity structure
  const envelopeValidation = (typeof SentinelIdentity !== "undefined")
    ? SentinelIdentity.validateEventEnvelope(message)
    : { valid: false, errors: ["SentinelIdentity unavailable"] };

  if (!envelopeValidation.valid) {
    console.warn("[SentinelGuard] Rejected invalid mouse event envelope:", envelopeValidation.errors);
    if (sendResponse) {
      sendResponse({ status: "REJECTED", errors: envelopeValidation.errors });
    }
    return;
  }

  // 2. Validate behavioral feature payload schema and numerical bounds
  const payloadValidation = (typeof SentinelMouseFeatures !== "undefined")
    ? SentinelMouseFeatures.validateFeatures(message.payload)
    : { valid: false, errors: ["SentinelMouseFeatures unavailable"] };

  if (!payloadValidation.valid) {
    console.warn("[SentinelGuard] Rejected invalid mouse feature payload:", payloadValidation.errors);
    if (sendResponse) {
      sendResponse({ status: "REJECTED", errors: payloadValidation.errors });
    }
    return;
  }

  // 3. Compact aggregated logging for development verification (strictly zero coordinate logging)
  console.log("[SentinelGuard] Mouse behavior event received.");
  console.log("[SentinelGuard] session_id:", message.session_id);
  console.log("[SentinelGuard] event_id:", message.event_id);
  console.log("[SentinelGuard] movement_count:", message.payload.movement_count);
  console.log("[SentinelGuard] average_velocity:", message.payload.average_velocity);
  console.log("[SentinelGuard] path_efficiency:", message.payload.path_efficiency);

  if (sendResponse) {
    sendResponse({ status: "ACK" });
  }
}

// Listen for structured runtime events from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || typeof message !== "object") {
    return;
  }

  const eventType = message.event_type || message.type;

  // Phase 3: Identity pipeline verification event
  if (eventType === "TEST_EVENT") {
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
    return;
  }

  // Handle direct protection state toggle from popup
  if (eventType === "SET_PROTECTION_STATE") {
    isProtectionEnabled = message.protectionEnabled !== false;
    console.log(`[SentinelGuard][DEBUG] Service worker received SET_PROTECTION_STATE: ${isProtectionEnabled}`);
    if (sendResponse) {
      sendResponse({ status: "ACK", protectionEnabled: isProtectionEnabled });
    }
    return;
  }

  // Phase 4: Mouse behavioral telemetry event
  if (eventType === "MOUSE_BEHAVIOR") {
    // Defense-in-depth: verify protection state synchronously and against storage
    if (!isProtectionEnabled) {
      console.log("[SentinelGuard][DEBUG] SW rejected MOUSE_BEHAVIOR: protection OFF (sync guard)");
      if (sendResponse) {
        sendResponse({ status: "REJECTED", reason: "PROTECTION_DISABLED" });
      }
      return;
    }

    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.get(["protectionEnabled"], (result) => {
        if (result && result.protectionEnabled === false) {
          isProtectionEnabled = false;
          console.log("[SentinelGuard][DEBUG] SW rejected MOUSE_BEHAVIOR: protection OFF (storage guard)");
          if (sendResponse) {
            sendResponse({ status: "REJECTED", reason: "PROTECTION_DISABLED" });
          }
          return;
        }

        if (!isProtectionEnabled) {
          console.log("[SentinelGuard][DEBUG] SW rejected MOUSE_BEHAVIOR: protection OFF (internal state)");
          if (sendResponse) {
            sendResponse({ status: "REJECTED", reason: "PROTECTION_DISABLED" });
          }
          return;
        }

        processMouseBehavior(message, sendResponse);
      });
      return true; // Keep message channel open for async response
    }

    processMouseBehavior(message, sendResponse);
    return;
  }
});
