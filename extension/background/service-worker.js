/**
 * SentinelGuard — Background Service Worker
 * 
 * Phase 2 Scope:
 * - Listens for one-way runtime messages from the content script.
 * - Validates and logs TEST_EVENT reception.
 * 
 * Safety & Privacy Notice:
 * - NO API requests or network calls
 * - NO event collection or buffering
 * - NO storage persistence
 * - NO machine learning integration
 * - NO authentication logic
 */

console.log("[SentinelGuard] Service worker initialized.");

chrome.runtime.onInstalled.addListener(() => {
  console.log("[SentinelGuard] Extension installed successfully.");
});

// Phase 2: Listen for test message from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === "TEST_EVENT") {
    console.log("[SentinelGuard] Test event received.");
    console.log("[SentinelGuard] Test event timestamp:", message.timestamp);
    if (sendResponse) {
      sendResponse({ status: "ACK" });
    }
  }
});
