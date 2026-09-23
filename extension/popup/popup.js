/**
 * SentinelGuard — Popup Script (Scaffold)
 * 
 * Phase 1 Scope:
 * - Handles simple UI toggle feedback for visual verification.
 * - Confirms popup initialization via console logging.
 * 
 * Safety & Privacy Notice:
 * - NO persistent state storage in Phase 1
 * - NO behavioral tracking or signal capture
 * - NO API requests
 */

document.addEventListener("DOMContentLoaded", () => {
  console.log("[SentinelGuard] Popup loaded.");

  const toggle = document.getElementById("protection-toggle");
  const statusValue = document.getElementById("status-value");
  const statusBadge = document.getElementById("status-badge");

  if (!toggle || !statusValue || !statusBadge) {
    return;
  }

  function updateUI(isEnabled) {
    toggle.checked = isEnabled;
    if (isEnabled) {
      statusValue.textContent = "ON";
      statusValue.classList.remove("off");
      statusBadge.textContent = "ACTIVE";
      statusBadge.classList.remove("badge-inactive");
      statusBadge.classList.add("badge-active");
      console.log("[SentinelGuard] Protection toggled to visual ON state.");
    } else {
      statusValue.textContent = "OFF";
      statusValue.classList.add("off");
      statusBadge.textContent = "PAUSED";
      statusBadge.classList.remove("badge-active");
      statusBadge.classList.add("badge-inactive");
      console.log("[SentinelGuard] Protection toggled to visual OFF state.");
    }
  }

  // Load persistent protection state (defaults to true if unset)
  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(["protectionEnabled"], (result) => {
      if (chrome.runtime.lastError) {
        console.warn("[SentinelGuard] Failed to load protection state:", chrome.runtime.lastError);
        return;
      }
      const isEnabled = result && "protectionEnabled" in result ? result.protectionEnabled !== false : true;
      updateUI(isEnabled);
    });
  }

  toggle.addEventListener("change", (e) => {
    const isChecked = Boolean(e.target.checked);
    updateUI(isChecked);

    console.log("[SentinelGuard][POPUP] Toggle switched to:", isChecked);

    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ protectionEnabled: isChecked }, () => {
        if (chrome.runtime.lastError) {
          console.warn("[SentinelGuard] Failed to persist protection state:", chrome.runtime.lastError);
        } else {
          // Immediately verify storage persistence
          chrome.storage.local.get(["protectionEnabled"], (verified) => {
            console.log("[SentinelGuard][POPUP] Verified storage protectionEnabled:", verified ? verified.protectionEnabled : "unset");
          });
        }
      });
    }

    // Direct background service worker messaging for immediate synchronization
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage) {
      try {
        chrome.runtime.sendMessage({
          type: "SET_PROTECTION_STATE",
          protectionEnabled: isChecked
        }, () => {
          if (chrome.runtime.lastError) {
            // Suppress error when service worker is spinning up
          }
        });
      } catch (err) {
        // Suppress messaging errors
      }
    }

    // Direct active-tab messaging for instantaneous zero-latency reaction
    if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.query) {
      try {
        chrome.tabs.query({}, (tabs) => {
          if (!chrome.runtime.lastError && Array.isArray(tabs)) {
            for (const tab of tabs) {
              if (tab && tab.id) {
                chrome.tabs.sendMessage(tab.id, {
                  type: "SET_PROTECTION_STATE",
                  protectionEnabled: isChecked
                }, () => {
                  if (chrome.runtime.lastError) {
                    // Suppress error for tabs where content script is not injected
                  }
                });
              }
            }
          }
        });
      } catch (tabsErr) {
        // Suppress tabs query error
      }
    }
  });
});
