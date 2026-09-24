/**
 * SentinelGuard — Content Script
 * 
 * Phase 3 Scope:
 * - Session and event identity initialization using SentinelIdentity utility.
 * - Dispatches a structured TEST_EVENT envelope over runtime messaging.
 * 
 * Phase 4 Scope:
 * - Passive, throttled mouse movement listener (50 ms / ~20 Hz sampling).
 * - Ephemeral in-memory movement buffer (max 25 points, idle timeout 500 ms).
 * - Client-side behavioral feature extraction via SentinelMouseFeatures.
 * - Dispatches structured MOUSE_BEHAVIOR event envelope via chrome.runtime.sendMessage().
 * - Real-time protection state synchronization with chrome.storage.local.
 * 
 * Safety & Privacy Notice:
 * - Raw mouse coordinates exist ONLY in ephemeral memory during the active sampling window.
 * - Raw coordinates are NEVER persisted, NEVER logged, and NEVER transmitted over IPC.
 * - NO keystroke or typing timing tracking (Phase 5).
 * - NO form value, password, or credential access.
 * - NO DOM reading or scraping.
 * - NO network or API transmission (zero fetch, zero XHR, zero WebSocket).
 */

console.log("[SentinelGuard] Content script loaded.");

// ============================================================
// Chrome Extension Context Lifecycle Safety Helpers
// ============================================================

/**
 * Checks whether the Chrome extension context is still valid.
 * When an extension is reloaded/updated, existing content scripts are orphaned,
 * causing chrome.runtime.id to become undefined.
 */
function isExtensionContextValid() {
  try {
    return (
      typeof chrome !== "undefined" &&
      Boolean(chrome.runtime) &&
      typeof chrome.runtime.id === "string" &&
      chrome.runtime.id.length > 0
    );
  } catch (e) {
    return false;
  }
}

/**
 * Checks if a caught error represents a destroyed extension context.
 */
function isContextInvalidatedError(error) {
  return (
    error instanceof Error &&
    typeof error.message === "string" &&
    error.message.includes("Extension context invalidated")
  );
}

/**
 * Handles extension context invalidation gracefully by cleaning up timers,
 * purging buffers, and unregistering DOM listeners without throwing uncaught errors.
 */
function handleContextInvalidated() {
  resetMouseTracking();
  try {
    window.removeEventListener("mousemove", handleMouseMove, { passive: true });
  } catch (e) {
    // Suppress listener removal errors in dead context
  }
}

// Generate an isolated, opaque session ID for this page observation lifecycle
const currentSessionId = (typeof SentinelIdentity !== "undefined")
  ? SentinelIdentity.generateSessionId()
  : ("sess_" + crypto.randomUUID());

// Construct a structured development test event envelope (Phase 3 preservation)
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

if (isExtensionContextValid()) {
  try {
    chrome.runtime.sendMessage(testPayload, () => {
      if (chrome.runtime.lastError) {
        // Suppress or handle if background worker is spinning up
      }
    });
  } catch (err) {
    if (isContextInvalidatedError(err)) {
      handleContextInvalidated();
    } else {
      throw err;
    }
  }
}

console.log("[SentinelGuard] Test event sent.");

// ============================================================
// Phase 4: Mouse Behavioral Telemetry Collection
// ============================================================

// Protection state tracking (synchronized with extension popup toggle)
let isProtectionEnabled = true;

// Sampling and buffering configuration
// 50 ms (~20 Hz) is an engineering trade-off: comfortably covers human motor
// dynamics (5-15 Hz band) while preventing listener thrashing on high-polling mice.
const SAMPLE_INTERVAL_MS = 50;
const MAX_BUFFER_SIZE = 25;
const IDLE_TIMEOUT_MS = 500;

// Ephemeral in-memory state
let movementBuffer = [];
let lastSampleTime = 0;
let idleTimer = null;

/**
 * Resets the in-memory coordinate buffer and cancels any pending emission timer.
 */
function resetMouseTracking() {
  if (idleTimer !== null) {
    clearTimeout(idleTimer);
    idleTimer = null;
  }
  movementBuffer = [];
  lastSampleTime = 0;
}

/**
 * Flushes the ephemeral movement buffer: extracts 10 behavioral features,
 * discards raw coordinates, wraps features in the event envelope, and dispatches.
 */
function flushMovementBuffer() {
  if (idleTimer !== null) {
    clearTimeout(idleTimer);
    idleTimer = null;
  }

  // Gracefully stop if the extension context was invalidated
  if (!isExtensionContextValid()) {
    handleContextInvalidated();
    return;
  }

  // Immediate synchronous guard: if protection is disabled, purge immediately without emitting
  if (!isProtectionEnabled) {
    resetMouseTracking();
    return;
  }

  // Insufficient points (< 2) cannot form a kinematic trajectory
  if (movementBuffer.length < 2) {
    resetMouseTracking();
    return;
  }

  // Snapshot coordinate buffer and immediately purge raw coordinates from memory
  const samples = movementBuffer;
  movementBuffer = [];

  if (typeof SentinelMouseFeatures === "undefined" || typeof SentinelIdentity === "undefined") {
    return;
  }

  // Pure mathematical feature extraction (zero coordinate leakage)
  const features = SentinelMouseFeatures.calculateFeatures(samples);
  if (!features) {
    return;
  }

  // Second synchronous guard: if protection was toggled off during calculation, abort
  if (!isProtectionEnabled) {
    resetMouseTracking();
    return;
  }

  // Construct structured event envelope using Phase 3 identity API
  // Note: Option 'data' maps to envelope.payload
  const envelope = SentinelIdentity.createEventEnvelope({
    sessionId: currentSessionId,
    eventType: "MOUSE_BEHAVIOR",
    data: features
  });

  // Check extension context validity before attempting asynchronous storage query
  if (!isExtensionContextValid()) {
    handleContextInvalidated();
    return;
  }

  // Asynchronous pre-flight check directly against storage before network IPC
  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    try {
      chrome.storage.local.get(["protectionEnabled"], (result) => {
        // Re-verify context within asynchronous callback
        if (!isExtensionContextValid()) {
          handleContextInvalidated();
          return;
        }

        if (result && result.protectionEnabled === false) {
          isProtectionEnabled = false;
          resetMouseTracking();
          return;
        }

        if (!isProtectionEnabled) {
          resetMouseTracking();
          return;
        }

        try {
          chrome.runtime.sendMessage(envelope, () => {
            if (chrome.runtime.lastError) {
              // Suppress when background service worker is dormant
            }
          });
        } catch (sendErr) {
          if (isContextInvalidatedError(sendErr)) {
            handleContextInvalidated();
            return;
          }
          throw sendErr;
        }
      });
    } catch (storageErr) {
      if (isContextInvalidatedError(storageErr)) {
        handleContextInvalidated();
        return;
      }
      throw storageErr;
    }
  } else {
    try {
      chrome.runtime.sendMessage(envelope, () => {
        if (chrome.runtime.lastError) {
          // Suppress when background service worker is dormant
        }
      });
    } catch (sendErr) {
      if (isContextInvalidatedError(sendErr)) {
        handleContextInvalidated();
        return;
      }
      throw sendErr;
    }
  }
}

/**
 * Throttled passive mouse movement listener.
 */
function handleMouseMove(e) {
  // If extension context has been invalidated (e.g. extension reload), tear down gracefully
  if (!isExtensionContextValid()) {
    handleContextInvalidated();
    return;
  }

  if (!isProtectionEnabled) {
    resetMouseTracking();
    return;
  }

  const now = Date.now();
  if (now - lastSampleTime < SAMPLE_INTERVAL_MS) {
    return;
  }
  lastSampleTime = now;

  const clientX = typeof e.clientX === "number" && Number.isFinite(e.clientX) ? e.clientX : 0;
  const clientY = typeof e.clientY === "number" && Number.isFinite(e.clientY) ? e.clientY : 0;

  movementBuffer.push({ x: clientX, y: clientY, t: now });

  // Reset idle timer for movement gesture demarcation
  if (idleTimer !== null) {
    clearTimeout(idleTimer);
  }

  if (movementBuffer.length >= MAX_BUFFER_SIZE) {
    flushMovementBuffer();
  } else {
    idleTimer = setTimeout(flushMovementBuffer, IDLE_TIMEOUT_MS);
  }
}

// Synchronize initial protection state from chrome.storage.local
if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local && isExtensionContextValid()) {
  try {
    chrome.storage.local.get(["protectionEnabled"], (result) => {
      if (!isExtensionContextValid()) {
        handleContextInvalidated();
        return;
      }
      if (!chrome.runtime.lastError && result && "protectionEnabled" in result) {
        isProtectionEnabled = result.protectionEnabled !== false;
        if (!isProtectionEnabled) {
          resetMouseTracking();
        }
      }
      console.log("[SentinelGuard][DEBUG] Initial protection state:", isProtectionEnabled);
    });

    // Listen for real-time toggle changes from popup UI across all storage namespaces
    chrome.storage.onChanged.addListener((changes) => {
      if (!isExtensionContextValid()) {
        handleContextInvalidated();
        return;
      }
      if (changes && "protectionEnabled" in changes) {
        const oldVal = changes.protectionEnabled.oldValue;
        const newVal = changes.protectionEnabled.newValue;
        isProtectionEnabled = newVal !== false;
        console.log(`[SentinelGuard][DEBUG] Protection state changed: ${oldVal} -> ${newVal}`);
        console.log(`[SentinelGuard][DEBUG] Internal protection state: ${isProtectionEnabled}`);
        if (!isProtectionEnabled) {
          resetMouseTracking();
        }
      }
    });
  } catch (storageInitErr) {
    if (isContextInvalidatedError(storageInitErr)) {
      handleContextInvalidated();
    } else {
      throw storageInitErr;
    }
  }
}

// Listen for direct runtime notifications from popup for instantaneous zero-latency reaction
if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage && isExtensionContextValid()) {
  try {
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
      if (!isExtensionContextValid()) {
        handleContextInvalidated();
        return;
      }
      if (msg && msg.type === "SET_PROTECTION_STATE") {
        isProtectionEnabled = msg.protectionEnabled !== false;
        console.log(`[SentinelGuard][DEBUG] Content received SET_PROTECTION_STATE: ${isProtectionEnabled}`);
        if (!isProtectionEnabled) {
          resetMouseTracking();
        }
        if (sendResponse) {
          sendResponse({ status: "ACK", isProtectionEnabled });
        }
      }
    });
  } catch (msgInitErr) {
    if (isContextInvalidatedError(msgInitErr)) {
      handleContextInvalidated();
    } else {
      throw msgInitErr;
    }
  }
}

// ============================================================
// Session ID Bridge for Demo Login Page
// ============================================================
// Allows the demo login page to request the current session ID
// via window.postMessage. Only shares the opaque UUID — no internal
// extension state or API surface is exposed.

window.addEventListener("message", (event) => {
  if (event.source !== window) return;
  if (event.data && event.data.type === "SentinelGuard:RequestSessionId") {
    window.postMessage({
      type: "SentinelGuard:SessionId",
      sessionId: currentSessionId
    }, "*");
  }
});

// Register passive mousemove listener on window
window.addEventListener("mousemove", handleMouseMove, { passive: true });

