/**
 * SentinelGuard — Mouse Behavioral Features Utility
 *
 * Phase 4 Scope:
 * - Mathematical extraction of 10 privacy-conscious behavioral features from
 *   ephemeral cursor coordinate samples.
 * - Validation of feature structures and numerical boundaries.
 *
 * Safety & Privacy Notice:
 * - Operates purely on ephemeral coordinate buffers in memory.
 * - Raw coordinates are NEVER stored, logged, or returned in feature outputs.
 * - Returns ONLY compact derived statistical & kinematic metrics.
 * - Robust numerical guarding: guarantees zero NaN, zero Infinity, zero division-by-zero.
 */

(function (root) {
  "use strict";

  /**
   * Euclidean distance between two points.
   */
  function euclideanDistance(p1, p2) {
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  /**
   * Calculates the perpendicular distance from point p to the line segment connecting start and end.
   * If start and end are identical (zero-length chord), returns Euclidean distance to start.
   */
  function perpendicularDistance(p, start, end) {
    const chordLength = euclideanDistance(start, end);
    if (chordLength === 0) {
      return euclideanDistance(p, start);
    }
    // Line formula: |(y2 - y1)*x0 - (x2 - x1)*y0 + x2*y1 - y2*x1| / chordLength
    const numerator = Math.abs(
      (end.y - start.y) * p.x - (end.x - start.x) * p.y + end.x * start.y - end.y * start.x
    );
    return numerator / chordLength;
  }

  /**
   * Normalizes an angle difference to the range [0, Math.PI].
   */
  function normalizeAngleDiff(angle1, angle2) {
    let diff = Math.abs(angle1 - angle2);
    while (diff > Math.PI) {
      diff = Math.abs(diff - 2 * Math.PI);
    }
    return diff;
  }

  /**
   * Rounds a finite number to 4 decimal places to avoid floating point noise.
   */
  function round4(val) {
    if (!Number.isFinite(val)) {
      return 0.0;
    }
    return Math.round(val * 10000) / 10000;
  }

  /**
   * Extracts 10 behavioral biometrics features from an array of sampled movement points.
   * Expected sample format: [ { x: number, y: number, t: number }, ... ]
   *
   * @param {Array<Object>} samples - Array of sampled mouse positions with timestamps.
   * @returns {Object|null} Extracted features object, or null if insufficient points (< 2).
   */
  function calculateFeatures(samples) {
    if (!Array.isArray(samples) || samples.length < 2) {
      return null;
    }

    const n = samples.length;

    // Validate that all samples contain finite numbers
    for (let i = 0; i < n; i++) {
      const s = samples[i];
      if (
        !s ||
        typeof s.x !== "number" ||
        typeof s.y !== "number" ||
        typeof s.t !== "number" ||
        !Number.isFinite(s.x) ||
        !Number.isFinite(s.y) ||
        !Number.isFinite(s.t)
      ) {
        return null;
      }
    }

    const firstPoint = samples[0];
    const lastPoint = samples[n - 1];

    // 1. movement_duration (ms)
    // Elapsed time between the first and last sampled points.
    const rawDuration = lastPoint.t - firstPoint.t;
    const movement_duration = rawDuration > 0 ? Math.round(rawDuration) : 0;

    // Segment metrics computation
    let total_distance_raw = 0;
    const segmentVelocities = [];
    const segmentAngles = [];

    for (let i = 0; i < n - 1; i++) {
      const p1 = samples[i];
      const p2 = samples[i + 1];

      const dist = euclideanDistance(p1, p2);
      total_distance_raw += dist;

      const dt = p2.t - p1.t;
      // Instantaneous segment velocity in px/ms
      // Guard against division by zero if consecutive points share timestamp
      if (dt > 0) {
        segmentVelocities.push(dist / dt);
      } else {
        segmentVelocities.push(0.0);
      }

      // Record heading angle for segments with non-zero displacement
      if (dist > 0.0001) {
        segmentAngles.push({
          index: i,
          angle: Math.atan2(p2.y - p1.y, p2.x - p1.x)
        });
      }
    }

    // 2. total_distance (px)
    const total_distance = round4(total_distance_raw);

    // 3. average_velocity (px/ms)
    // Total distance divided by total elapsed duration.
    // Safe fallback 0.0 if duration <= 0 or distance == 0.
    const average_velocity =
      movement_duration > 0 && total_distance_raw > 0
        ? round4(total_distance_raw / movement_duration)
        : 0.0;

    // 4. maximum_velocity (px/ms)
    // Maximum observed instantaneous segment velocity.
    let maxVel = 0;
    for (let i = 0; i < segmentVelocities.length; i++) {
      if (segmentVelocities[i] > maxVel) {
        maxVel = segmentVelocities[i];
      }
    }
    const maximum_velocity = round4(maxVel);

    // 5. velocity_variance ((px/ms)^2)
    // Statistical sample variance of segment velocities.
    // Safe fallback 0.0 if fewer than 2 segments exist.
    let velocity_variance = 0.0;
    const m = segmentVelocities.length;
    if (m >= 2) {
      let sumVel = 0;
      for (let i = 0; i < m; i++) {
        sumVel += segmentVelocities[i];
      }
      const meanVel = sumVel / m;

      let sumSqDiff = 0;
      for (let i = 0; i < m; i++) {
        const diff = segmentVelocities[i] - meanVel;
        sumSqDiff += diff * diff;
      }
      velocity_variance = round4(sumSqDiff / m);
    }

    // 6. direction_change_count & 7. average_direction_change
    // Direction changes evaluated across consecutive non-stationary segments.
    // Threshold: angle deflection > pi / 6 radians (~30 degrees) represents a meaningful turn.
    const DIRECTION_CHANGE_THRESHOLD = Math.PI / 6;
    let direction_change_count = 0;
    let totalAngularChange = 0;
    let angleTransitions = 0;

    for (let i = 0; i < segmentAngles.length - 1; i++) {
      const a1 = segmentAngles[i].angle;
      const a2 = segmentAngles[i + 1].angle;
      const angleDiff = normalizeAngleDiff(a1, a2);

      totalAngularChange += angleDiff;
      angleTransitions++;

      if (angleDiff > DIRECTION_CHANGE_THRESHOLD) {
        direction_change_count++;
      }
    }

    const average_direction_change =
      angleTransitions > 0 ? round4(totalAngularChange / angleTransitions) : 0.0;

    // 8. path_efficiency
    // Direct Euclidean displacement divided by total traveled distance. Range: [0.0, 1.0].
    // If total traveled distance is zero, efficiency is 0.0.
    const directDisplacement = euclideanDistance(firstPoint, lastPoint);
    let path_efficiency = 0.0;
    if (total_distance_raw > 0) {
      const rawEff = directDisplacement / total_distance_raw;
      path_efficiency = round4(Math.min(1.0, Math.max(0.0, rawEff)));
    }

    // 9. straightness_ratio
    // Measures how closely intermediate points adhere to the direct chord connecting P_1 and P_N.
    // Definition: 1 - (max_perpendicular_deviation / direct_displacement).
    // Special case: If start and end points are identical (directDisplacement == 0),
    // the movement forms a closed loop or point-return; straightness is defined as 0.0.
    let straightness_ratio = 0.0;
    if (directDisplacement > 0.0001) {
      let maxPerpDev = 0;
      for (let i = 1; i < n - 1; i++) {
        const d = perpendicularDistance(samples[i], firstPoint, lastPoint);
        if (d > maxPerpDev) {
          maxPerpDev = d;
        }
      }
      const rawStraightness = 1.0 - maxPerpDev / directDisplacement;
      straightness_ratio = round4(Math.min(1.0, Math.max(0.0, rawStraightness)));
    } else {
      straightness_ratio = 0.0;
    }

    return {
      movement_count: n,
      total_distance,
      average_velocity,
      maximum_velocity,
      velocity_variance,
      direction_change_count,
      average_direction_change,
      path_efficiency,
      straightness_ratio,
      movement_duration
    };
  }

  /**
   * Validates a feature payload against schema and numerical constraints.
   *
   * @param {Object} payload - The feature dictionary to validate.
   * @returns {Object} { valid: boolean, errors: string[] }
   */
  function validateFeatures(payload) {
    const errors = [];

    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return { valid: false, errors: ["Feature payload must be a non-null object."] };
    }

    const requiredKeys = [
      "movement_count",
      "total_distance",
      "average_velocity",
      "maximum_velocity",
      "velocity_variance",
      "direction_change_count",
      "average_direction_change",
      "path_efficiency",
      "straightness_ratio",
      "movement_duration"
    ];

    for (let i = 0; i < requiredKeys.length; i++) {
      const key = requiredKeys[i];
      if (!(key in payload)) {
        errors.push(`Missing required feature key: '${key}'.`);
      } else {
        const val = payload[key];
        if (typeof val !== "number" || !Number.isFinite(val)) {
          errors.push(`Feature '${key}' must be a finite number. Received: ${val}.`);
        }
      }
    }

    if (errors.length > 0) {
      return { valid: false, errors };
    }

    // Numerical range and boundary validation
    if (!Number.isInteger(payload.movement_count) || payload.movement_count < 2) {
      errors.push("Feature 'movement_count' must be an integer >= 2.");
    }

    if (payload.total_distance < 0) {
      errors.push("Feature 'total_distance' must be non-negative.");
    }

    if (payload.average_velocity < 0) {
      errors.push("Feature 'average_velocity' must be non-negative.");
    }

    if (payload.maximum_velocity < 0) {
      errors.push("Feature 'maximum_velocity' must be non-negative.");
    }

    if (payload.velocity_variance < 0) {
      errors.push("Feature 'velocity_variance' must be non-negative.");
    }

    if (!Number.isInteger(payload.direction_change_count) || payload.direction_change_count < 0) {
      errors.push("Feature 'direction_change_count' must be a non-negative integer.");
    }

    if (payload.average_direction_change < 0 || payload.average_direction_change > Math.PI + 0.01) {
      errors.push("Feature 'average_direction_change' must be in range [0, pi].");
    }

    if (payload.path_efficiency < 0 || payload.path_efficiency > 1.0001) {
      errors.push("Feature 'path_efficiency' must be in range [0.0, 1.0].");
    }

    if (payload.straightness_ratio < 0 || payload.straightness_ratio > 1.0001) {
      errors.push("Feature 'straightness_ratio' must be in range [0.0, 1.0].");
    }

    if (payload.movement_duration < 0) {
      errors.push("Feature 'movement_duration' must be non-negative.");
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  const SentinelMouseFeatures = {
    calculateFeatures,
    validateFeatures,
    euclideanDistance,
    perpendicularDistance
  };

  root.SentinelMouseFeatures = SentinelMouseFeatures;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = SentinelMouseFeatures;
  }
})(typeof globalThis !== "undefined" ? globalThis : (typeof self !== "undefined" ? self : this));
