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

  toggle.addEventListener("change", (e) => {
    const isChecked = e.target.checked;

    if (isChecked) {
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
  });
});
