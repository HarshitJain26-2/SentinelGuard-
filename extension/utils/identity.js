/**
 * SentinelGuard — Identity & Event Envelope Utility
 *
 * Phase 3 Scope:
 * - Single source of truth for Session ID and Event ID generation.
 * - Event envelope construction and schema validation.
 *
 * Safety & Privacy Notice:
 * - Cryptographically random opaque identifiers (UUID v4) with zero PII.
 * - NO usernames, passwords, emails, IP addresses, or device IDs.
 * - NO DOM scraping or behavioral telemetry collection.
 */

(function (root) {
  "use strict";

  const PREFIX_SESSION = "sess_";
  const PREFIX_EVENT = "evt_";

  const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const SESSION_ID_REGEX = /^sess_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const EVENT_ID_REGEX = /^evt_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

  /**
   * Generates a standard RFC 4122 version 4 UUID.
   * Uses crypto.randomUUID() where available, with a cryptographic fallback.
   */
  function generateRawUUID() {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }
    if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
      const bytes = new Uint8Array(16);
      crypto.getRandomValues(bytes);
      bytes[6] = (bytes[6] & 0x0f) | 0x40; // Version 4
      bytes[8] = (bytes[8] & 0x3f) | 0x80; // Variant 10xx
      const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
      return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
    }
    throw new Error("[SentinelGuard] Cryptographically secure random number generator unavailable.");
  }

  /**
   * Generates a cryptographically random, opaque session ID.
   * Format: sess_<uuid-v4>
   */
  function generateSessionId() {
    return PREFIX_SESSION + generateRawUUID();
  }

  /**
   * Generates a cryptographically random, unique event ID.
   * Format: evt_<uuid-v4>
   */
  function generateEventId() {
    return PREFIX_EVENT + generateRawUUID();
  }

  /**
   * Validates whether a string is a valid session ID.
   */
  function isValidSessionId(id) {
    return typeof id === "string" && (SESSION_ID_REGEX.test(id) || UUID_REGEX.test(id));
  }

  /**
   * Validates whether a string is a valid event ID.
   */
  function isValidEventId(id) {
    return typeof id === "string" && (EVENT_ID_REGEX.test(id) || UUID_REGEX.test(id));
  }

  /**
   * Constructs a standard SentinelGuard event envelope.
   */
  function createEventEnvelope(options) {
    if (!options || typeof options !== "object") {
      throw new Error("[SentinelGuard] Options object required for createEventEnvelope.");
    }

    const { sessionId, eventType, timestamp, data } = options;

    if (!isValidSessionId(sessionId)) {
      throw new Error("[SentinelGuard] Invalid session_id provided for event envelope.");
    }

    if (!eventType || typeof eventType !== "string") {
      throw new Error("[SentinelGuard] Valid eventType string required.");
    }

    return {
      type: eventType,
      event_type: eventType,
      event_id: generateEventId(),
      session_id: sessionId,
      timestamp: typeof timestamp === "number" ? timestamp : Date.now(),
      payload: data && typeof data === "object" ? data : {}
    };
  }

  /**
   * Validates an event envelope against structural and security requirements.
   */
  function validateEventEnvelope(envelope) {
    const errors = [];

    if (!envelope || typeof envelope !== "object") {
      return { valid: false, errors: ["Event envelope must be a non-null object."] };
    }

    const eventType = envelope.event_type || envelope.type;
    if (!eventType || typeof eventType !== "string" || !/^[A-Z0-9_]+$/.test(eventType)) {
      errors.push("Invalid or missing event type (must be alphanumeric uppercase string).");
    }

    if (!isValidEventId(envelope.event_id)) {
      errors.push("Invalid or missing event_id (must match UUID v4 format).");
    }

    if (!isValidSessionId(envelope.session_id)) {
      errors.push("Invalid or missing session_id (must match UUID v4 format).");
    }

    const ts = envelope.timestamp;
    if (typeof ts !== "number" || !Number.isInteger(ts) || ts <= 0) {
      errors.push("Invalid or missing timestamp (must be a positive integer).");
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  const SentinelIdentity = {
    generateSessionId,
    generateEventId,
    createEventEnvelope,
    isValidSessionId,
    isValidEventId,
    validateEventEnvelope
  };

  root.SentinelIdentity = SentinelIdentity;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = SentinelIdentity;
  }
})(typeof globalThis !== "undefined" ? globalThis : (typeof self !== "undefined" ? self : this));
