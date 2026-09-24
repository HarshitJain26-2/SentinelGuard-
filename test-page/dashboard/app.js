/**
 * SentinelGuard — Security Dashboard Application
 *
 * Fetches data from:
 *   GET /api/security/stats/
 *   GET /api/security/logs/
 *
 * Read-only. Does not modify any security state.
 */

(function () {
  "use strict";

  const BACKEND_URL = "http://127.0.0.1:8000";
  const STATS_API = `${BACKEND_URL}/api/security/stats/`;
  const LOGS_API = `${BACKEND_URL}/api/security/logs/`;

  // DOM references
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");
  const refreshBtn = document.getElementById("refreshBtn");

  const totalEvents = document.getElementById("totalEvents");
  const totalDecisions = document.getElementById("totalDecisions");
  const totalAllowed = document.getElementById("totalAllowed");
  const totalOtp = document.getElementById("totalOtp");
  const totalBlocked = document.getElementById("totalBlocked");

  const barAllowed = document.getElementById("barAllowed");
  const barOtp = document.getElementById("barOtp");
  const barBlocked = document.getElementById("barBlocked");

  const logsBody = document.getElementById("logsBody");

  // ========================================
  // Data Fetching
  // ========================================

  async function fetchStats() {
    const response = await fetch(STATS_API);
    if (!response.ok) throw new Error(`Stats API returned ${response.status}`);
    return await response.json();
  }

  async function fetchLogs() {
    const response = await fetch(LOGS_API);
    if (!response.ok) throw new Error(`Logs API returned ${response.status}`);
    return await response.json();
  }

  // ========================================
  // Rendering
  // ========================================

  function renderStats(data) {
    const stats = data.stats;

    totalEvents.textContent = stats.total_events;
    totalDecisions.textContent = stats.total_decisions;
    totalAllowed.textContent = stats.allowed;
    totalOtp.textContent = stats.otp;
    totalBlocked.textContent = stats.blocked;

    // Risk distribution bar
    const total = stats.total_decisions || 1;
    const allowPct = (stats.allowed / total * 100).toFixed(1);
    const otpPct = (stats.otp / total * 100).toFixed(1);
    const blockPct = (stats.blocked / total * 100).toFixed(1);

    barAllowed.style.width = allowPct + "%";
    barAllowed.textContent = stats.allowed > 0 ? allowPct + "%" : "";

    barOtp.style.width = otpPct + "%";
    barOtp.textContent = stats.otp > 0 ? otpPct + "%" : "";

    barBlocked.style.width = blockPct + "%";
    barBlocked.textContent = stats.blocked > 0 ? blockPct + "%" : "";
  }

  function getRiskClass(score) {
    if (score < 0.30) return "risk-low";
    if (score < 0.70) return "risk-med";
    return "risk-high";
  }

  function getActionBadgeClass(action) {
    switch (action) {
      case "ALLOW": return "allow";
      case "OTP": return "otp";
      case "BLOCK": return "block";
      default: return "";
    }
  }

  function truncateSessionId(sid) {
    if (!sid || sid.length <= 20) return sid || "—";
    return sid.substring(0, 18) + "…";
  }

  function formatTimestamp(isoStr) {
    if (!isoStr) return "—";
    try {
      const d = new Date(isoStr);
      return d.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false
      });
    } catch {
      return isoStr;
    }
  }

  function renderLogs(data) {
    const logs = data.logs;

    if (!logs || logs.length === 0) {
      logsBody.innerHTML = '<tr><td colspan="6" class="empty-state">No security logs yet. Trigger a login attempt to generate data.</td></tr>';
      return;
    }

    logsBody.innerHTML = logs.map(log => `
      <tr>
        <td><span class="action-badge ${getActionBadgeClass(log.action_taken)}">${log.action_taken}</span></td>
        <td><span class="${getRiskClass(log.risk_score)}">${log.risk_score.toFixed(4)}</span></td>
        <td><span class="session-id" title="${log.session_id || ''}">${truncateSessionId(log.session_id)}</span></td>
        <td>${log.username_attempted || 'anonymous'}</td>
        <td><span class="reason-text" title="${log.reason || ''}">${log.reason || '—'}</span></td>
        <td><span class="timestamp">${formatTimestamp(log.timestamp)}</span></td>
      </tr>
    `).join("");
  }

  // ========================================
  // Connection Status
  // ========================================

  function setConnected() {
    statusDot.className = "status-dot connected";
    statusText.textContent = "Connected";
  }

  function setError(msg) {
    statusDot.className = "status-dot error";
    statusText.textContent = msg || "Disconnected";
  }

  // ========================================
  // Refresh
  // ========================================

  async function refreshDashboard() {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "↻ Loading...";

    try {
      const [statsData, logsData] = await Promise.all([fetchStats(), fetchLogs()]);
      renderStats(statsData);
      renderLogs(logsData);
      setConnected();
    } catch (err) {
      setError("Backend unreachable");
      logsBody.innerHTML = `<tr><td colspan="6" class="empty-state">Cannot reach backend at ${BACKEND_URL}. Is Django running?</td></tr>`;
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.textContent = "↻ Refresh";
    }
  }

  // ========================================
  // Init
  // ========================================

  refreshBtn.addEventListener("click", refreshDashboard);

  // Initial load
  refreshDashboard();

})();
