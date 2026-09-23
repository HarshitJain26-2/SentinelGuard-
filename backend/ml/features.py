"""
SentinelGuard — ML Feature Extraction & Validation Layer

Enforces strict feature ordering, numerical validity, and zero-PII privacy rules.
"""

import math
from typing import Dict, List, Any

FEATURE_NAMES = [
    "movement_count",
    "total_distance",
    "movement_duration",
    "average_velocity",
    "maximum_velocity",
    "velocity_variance",
    "direction_change_count",
    "average_direction_change",
    "path_efficiency",
    "straightness_ratio",
]

FORBIDDEN_KEYS = {"x", "y", "coordinates", "password", "key", "text", "raw"}


class FeatureExtractionError(ValueError):
    """Raised when an event payload fails validation or feature extraction."""
    pass


def validate_payload_privacy(payload: Dict[str, Any]) -> None:
    """
    Enforces privacy by rejecting payloads that contain raw coordinates or credentials.
    """
    if not isinstance(payload, dict):
        raise FeatureExtractionError("Payload must be a dictionary.")

    forbidden_found = set(payload.keys()) & FORBIDDEN_KEYS
    if forbidden_found:
        raise FeatureExtractionError(
            f"Privacy violation: payload contains forbidden key(s): {', '.join(sorted(forbidden_found))}"
        )


def extract_features_from_payload(payload: Dict[str, Any]) -> List[float]:
    """
    Extracts the 10 mouse behavioral features in the strict model-expected order.
    
    Returns:
        List[float]: 10 numeric feature values.
        
    Raises:
        FeatureExtractionError: If any required feature is missing, non-numeric,
                                or if raw coordinates/sensitive keys are present.
    """
    validate_payload_privacy(payload)

    feature_values: List[float] = []

    for name in FEATURE_NAMES:
        if name not in payload:
            raise FeatureExtractionError(f"Missing required feature: '{name}'.")

        val = payload[name]

        # In Python, isinstance(True, int) is True, so check for bool explicitly
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise FeatureExtractionError(
                f"Feature '{name}' must be numeric (int/float), got {type(val).__name__}."
            )

        float_val = float(val)

        if not math.isfinite(float_val):
            raise FeatureExtractionError(
                f"Feature '{name}' must be a finite number, got {float_val}."
            )

        feature_values.append(float_val)

    return feature_values
