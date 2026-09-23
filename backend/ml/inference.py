"""
SentinelGuard — ML Model Loading & Risk Inference Layer

Loads the trained model.joblib once as a cached singleton.
Validates input feature vectors against strict schema and ordering.
Produces risk probability in [0.0, 1.0] for class 1 (bot-like).
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd

from .features import FEATURE_NAMES, extract_features_from_payload, FeatureExtractionError

CURRENT_DIR = Path(__file__).resolve().parent
MODEL_PATH = CURRENT_DIR / "model.joblib"

_CACHED_MODEL = None


def get_model(model_path: Path = None):
    """
    Loads and caches the trained scikit-learn model singleton.
    """
    global _CACHED_MODEL
    target_path = Path(model_path) if model_path else MODEL_PATH

    if _CACHED_MODEL is None or model_path is not None:
        if not target_path.exists():
            raise FileNotFoundError(
                f"Trained model artifact not found at {target_path}. "
                "Please run 'python backend/ml/train_model.py' to generate model.joblib."
            )
        model = joblib.load(target_path)
        if model_path is None:
            _CACHED_MODEL = model
        return model

    return _CACHED_MODEL


def predict_risk(feature_vector: List[float], model_path: Path = None) -> float:
    """
    Calculates the bot risk score for a single 10-feature vector.
    
    Args:
        feature_vector: List of 10 numeric values matching FEATURE_NAMES order.
        model_path: Optional custom model artifact path.
        
    Returns:
        float: Risk score between 0.0 (highly human) and 1.0 (highly bot-like).
    """
    if not isinstance(feature_vector, (list, tuple, np.ndarray)):
        raise TypeError(f"Expected feature_vector as list/tuple, got {type(feature_vector).__name__}")

    if len(feature_vector) != len(FEATURE_NAMES):
        raise ValueError(
            f"Expected {len(FEATURE_NAMES)} features, received {len(feature_vector)}. "
            f"Required order: {FEATURE_NAMES}"
        )

    # Validate all elements are finite floats
    numeric_vector = [float(x) for x in feature_vector]
    for idx, val in enumerate(numeric_vector):
        if not np.isfinite(val):
            raise ValueError(f"Feature at index {idx} ({FEATURE_NAMES[idx]}) is not finite: {val}")

    model = get_model(model_path)

    # Reshape for single-sample prediction with feature names: shape (1, 10)
    X = pd.DataFrame([numeric_vector], columns=FEATURE_NAMES)

    # predict_proba returns [prob_class_0, prob_class_1]
    # Class 1 = bot probability -> risk score
    probabilities = model.predict_proba(X)
    bot_probability = float(probabilities[0][1])

    return max(0.0, min(1.0, round(bot_probability, 4)))



def extract_reasons(feature_vector: List[float], risk_score: float) -> Dict[str, Any]:
    """
    Generates explainability metadata identifying key factors contributing to the score.
    """
    reasons = {}
    f_dict = dict(zip(FEATURE_NAMES, feature_vector))

    # Identify anomalous or indicative signals
    if f_dict.get("path_efficiency", 0) > 0.94:
        reasons["path_efficiency"] = "Extremely high path straightness (characteristic of linear scripting)"
    elif f_dict.get("path_efficiency", 1) < 0.60:
        reasons["path_efficiency"] = "Unusually low path efficiency with erratic wander"

    if f_dict.get("velocity_variance", 0) < 0.008:
        reasons["velocity_variance"] = "Unnaturally constant cursor velocity"
    elif f_dict.get("velocity_variance", 0) > 0.08:
        reasons["velocity_variance"] = "High erratic velocity variance"

    if f_dict.get("direction_change_count", 0) <= 1:
        reasons["direction_changes"] = "Negligible direction adjustments during trajectory"
    elif f_dict.get("direction_change_count", 0) >= 9:
        reasons["direction_changes"] = "High frequency of abrupt direction changes"

    if f_dict.get("average_direction_change", 0) < 0.15:
        reasons["direction_angle"] = "Near-zero angular deflection across trajectory"

    if not reasons:
        reasons["behavioral_profile"] = "Nominal human kinematic baseline" if risk_score < 0.5 else "Anomalous multi-feature kinematic pattern"

    return reasons
