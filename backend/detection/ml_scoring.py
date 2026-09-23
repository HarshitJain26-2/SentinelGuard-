"""
SentinelGuard — ML Scoring Service Layer

Connects Django Event persistence to the scikit-learn ML inference pipeline.
Extracts features, evaluates risk score (0.0 - 1.0), and persists/updates the Score record.
Guarantees fault-isolation: inference errors are logged cleanly without failing event ingestion.
"""

import logging
from typing import Optional

from .models import Event, Score
from ml.features import extract_features_from_payload, FeatureExtractionError
from ml.inference import predict_risk, extract_reasons

logger = logging.getLogger(__name__)


def score_event(event: Event) -> Optional[Score]:
    """
    Evaluates behavioral risk for a stored MOUSE_BEHAVIOR event using the trained ML model.

    Args:
        event: An ingested Event instance with validated payload.

    Returns:
        Optional[Score]: The created or updated Score record, or None if scoring was skipped or failed.
    """
    if not event or event.event_type != "MOUSE_BEHAVIOR":
        logger.debug(
            "Skipping ML scoring for non-mouse event '%s' (id: %s).",
            getattr(event, "event_type", None),
            getattr(event, "event_id", None)
        )
        return None

    try:
        payload = event.payload
        if not payload or not isinstance(payload, dict):
            logger.warning(
                "Event %s missing dictionary payload; skipping ML scoring.",
                event.event_id
            )
            return None

        # 1. Feature extraction & numerical validation
        features = extract_features_from_payload(payload)

        # 2. ML model prediction (bot probability in [0.0, 1.0])
        risk_score = predict_risk(features)

        # 3. Explainability reasoning
        reasons = extract_reasons(features, risk_score)

        # 4. Idempotent persistence into Score model
        score, created = Score.objects.update_or_create(
            session=event.session,
            defaults={
                "event": event,
                "risk_score": risk_score,
                "reasons": reasons,
            }
        )

        logger.info(
            "ML scoring completed for event %s (session %s): risk_score=%.4f (created=%s)",
            event.event_id,
            event.session.session_id,
            risk_score,
            created
        )
        return score

    except FeatureExtractionError as fee:
        logger.warning(
            "Feature extraction rejected event %s: %s",
            getattr(event, "event_id", "unknown"),
            str(fee)
        )
        return None

    except Exception as exc:
        logger.error(
            "Unexpected error during ML scoring for event %s: %s",
            getattr(event, "event_id", "unknown"),
            str(exc),
            exc_info=True
        )
        return None
