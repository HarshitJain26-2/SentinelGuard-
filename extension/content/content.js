/**
 * SentinelGuard — Content Script
 * 
 * Phase 2 Scope:
 * - Content-script-to-service-worker one-way runtime messaging verification.
 * - Dispatches a single minimal test event to verify communication channel.
 * 
 * Safety & Privacy Notice:
 * - NO mouse movement tracking
 * - NO keystroke or typing timing tracking
 * - NO form value, password, or credential access
 * - NO DOM reading or scraping
 * - NO network or API transmission
 */

console.log("[SentinelGuard] Content script loaded.");

// Phase 2: Send a minimal, safe test event to service worker
const testPayload = {
  type: "TEST_EVENT",
  timestamp: Date.now()
};

chrome.runtime.sendMessage(testPayload, () => {
  if (chrome.runtime.lastError) {
    // Suppress or handle if background worker is spinning up
  }
});

console.log("[SentinelGuard] Test event sent.");
