"""
SentinelGuard — Adaptive Security Policy & Decision Engine

Evaluates server-authoritative risk scores against strict policy thresholds.
Manages step-up OTP challenge lifecycle, attempt throttling, and audit logging.
Strictly ignores any client-supplied risk scores.
"""

import math
import secrets
import logging
from datetime import timedelta
from typing import Tuple, Dict, Any, Optional

from django.utils import timezone
from detection.models import Session, Score, Decision
from .models import SecurityLog, OTPChallenge

logger = logging.getLogger(__name__)

# Strict Policy Thresholds
LOW_RISK_THRESHOLD = 0.30   # < 0.30 -> ALLOW
HIGH_RISK_THRESHOLD = 0.70  # >= 0.70 -> BLOCK; [0.30, 0.70) -> OTP
FALLBACK_RISK_SCORE = 0.50  # Neutral fallback when server score is unavailable


def evaluate_policy_action(risk_score: float) -> str:
    """
    Evaluates policy action strictly without pre-rounding.
      risk_score < 0.30       -> ALLOW
      0.30 <= risk_score < 0.70 -> OTP
      risk_score >= 0.70      -> BLOCK
    """
    if risk_score < LOW_RISK_THRESHOLD:
        return "ALLOW"
    elif risk_score >= HIGH_RISK_THRESHOLD:
        return "BLOCK"
    else:
        return "OTP"


def create_otp_challenge(session: Session, user=None) -> Tuple[OTPChallenge, str]:
    """
    Creates a new 5-minute, 3-attempt OTP challenge for a session.
    Stores salted hash in database and prints clear development-only log.
    
    Returns:
        Tuple[OTPChallenge, str]: (challenge model instance, plaintext otp for logging/testing)
    """
    # Invalidate previous unverified challenges for this session
    OTPChallenge.objects.filter(session=session, is_verified=False).delete()

    # Generate cryptographically secure 6-digit code
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = timezone.now() + timedelta(minutes=OTPChallenge.LIFETIME_MINUTES)

    challenge = OTPChallenge(
        session=session,
        user=user,
        expires_at=expires_at
    )
    challenge.set_otp(code)
    challenge.save()

    # Development-only console notification (never returned via production APIs)
    print(
        f"\n[DEVELOPMENT ONLY] SentinelGuard OTP Generated:\n"
        f"  Session:      {session.session_id}\n"
        f"  Challenge ID: {challenge.id}\n"
        f"  Code:         {code}\n"
        f"  Expires:      {expires_at.strftime('%H:%M:%S UTC')}\n"
    )

    return challenge, code


def process_login_attempt(
    session_id: str,
    username: str = "anonymous",
    ip_address: Optional[str] = None
) -> Tuple[str, Dict[str, Any], int]:
    """
    Authoritative server-side adaptive security evaluation.
    
    CRITICAL SECURITY INVARIANT:
    Retrieves the authoritative risk score strictly from the database.
    Never accepts, trusts, or references any client-supplied risk score.
    
    Returns:
        Tuple[action_str, response_dict, http_status_code]
    """
    clean_session_id = str(session_id or "").strip()
    session = None
    server_score = None
    is_fallback = False

    if clean_session_id:
        session = Session.objects.filter(session_id=clean_session_id).first()
        if session:
            server_score = getattr(session, "score", None)

    # Determine authoritative risk score
    if server_score is not None and math.isfinite(server_score.risk_score):
        risk_score = float(server_score.risk_score)
        reasons_list = []
        if isinstance(server_score.reasons, dict):
            reasons_list = [f"{k}: {v}" for k, v in server_score.reasons.items()]
        reason = ", ".join(reasons_list) if reasons_list else "Authoritative behavioral evaluation"
    else:
        # Documented fallback: when server risk score is unavailable, default to OTP challenge
        risk_score = FALLBACK_RISK_SCORE
        is_fallback = True
        reason = "Server risk score unavailable - defaulting to step-up OTP challenge (fallback policy)"

    action = evaluate_policy_action(risk_score)

    # Audit logging in SecurityLog
    log_entry = SecurityLog.objects.create(
        session=session,
        session_id_raw=clean_session_id,
        username_attempted=username or "anonymous",
        ip_address=ip_address,
        risk_score=risk_score,
        action_taken=action,
        reason=reason
    )

    # Sync with detection app Decision model and Score tier if session exists
    if session:
        tier_mapping = {"ALLOW": "allow", "OTP": "otp", "BLOCK": "block"}
        Decision.objects.create(
            session=session,
            action_taken=tier_mapping.get(action, "otp")
        )
        if server_score and not is_fallback:
            server_score.tier = tier_mapping.get(action, "otp")
            server_score.save(update_fields=["tier"])

    # Prepare structured decision response
    if action == "ALLOW":
        return action, {
            "action": "ALLOW",
            "risk_score": risk_score,
            "message": "Access granted."
        }, 200

    elif action == "OTP":
        if not session:
            # Create session on the fly if needed for fallback challenge tracking
            session, _ = Session.objects.get_or_create(session_id=clean_session_id or "sess_unregistered")

        challenge, _ = create_otp_challenge(session=session)
        return action, {
            "action": "OTP",
            "risk_score": risk_score,
            "challenge_id": str(challenge.id),
            "expires_at": challenge.expires_at.isoformat(),
            "message": "OTP step-up authentication required."
        }, 202

    else:  # BLOCK
        return action, {
            "action": "BLOCK",
            "risk_score": risk_score,
            "message": "Access blocked due to high behavioral risk."
        }, 403


def verify_otp_challenge(
    challenge_id: str,
    otp_input: str,
    ip_address: Optional[str] = None
) -> Tuple[bool, Dict[str, Any], int]:
    """
    Verifies a user-supplied 6-digit OTP against an active OTPChallenge.
    Throttles incorrect attempts (max 3) and enforces expiration (5 minutes).
    
    Returns:
        Tuple[is_success, response_dict, http_status_code]
    """
    clean_challenge_id = str(challenge_id or "").strip()
    clean_otp = str(otp_input or "").strip()

    challenge = OTPChallenge.objects.filter(id=clean_challenge_id).first()
    if not challenge:
        return False, {"status": "FAILED", "error": "Invalid or expired challenge ID."}, 400

    if challenge.is_verified:
        return False, {"status": "FAILED", "error": "Challenge has already been verified and cannot be reused."}, 400

    if timezone.now() >= challenge.expires_at:
        return False, {"status": "FAILED", "error": "OTP challenge has expired."}, 400

    if challenge.attempts >= challenge.MAX_ATTEMPTS:
        return False, {"status": "FAILED", "error": "Maximum verification attempts exceeded. Challenge locked."}, 403

    if challenge.check_otp(clean_otp):
        # Successful verification
        challenge.is_verified = True
        challenge.save(update_fields=["is_verified"])

        # Retrieve authoritative risk_score from the Score model for this session
        session_score = getattr(challenge.session, "score", None)
        authoritative_risk = (
            float(session_score.risk_score)
            if session_score is not None
            else FALLBACK_RISK_SCORE
        )

        SecurityLog.objects.create(
            session=challenge.session,
            session_id_raw=challenge.session.session_id,
            username_attempted=getattr(challenge.user, "username", "anonymous"),
            ip_address=ip_address,
            risk_score=authoritative_risk,
            action_taken="ALLOW",
            reason="Step-up OTP challenge verified successfully"
        )

        Decision.objects.create(
            session=challenge.session,
            action_taken="allow"
        )

        return True, {
            "status": "SUCCESS",
            "action": "ALLOW",
            "message": "OTP verified successfully."
        }, 200

    else:
        # Failed attempt
        challenge.attempts += 1
        challenge.save(update_fields=["attempts"])

        attempts_left = max(0, challenge.MAX_ATTEMPTS - challenge.attempts)
        if attempts_left == 0:
            SecurityLog.objects.create(
                session=challenge.session,
                session_id_raw=challenge.session.session_id,
                username_attempted=getattr(challenge.user, "username", "anonymous"),
                ip_address=ip_address,
                risk_score=1.0,
                action_taken="BLOCK",
                reason="Maximum OTP verification attempts exceeded - challenge locked"
            )
            return False, {
                "status": "FAILED",
                "error": "Maximum verification attempts exceeded. Challenge locked.",
                "attempts_remaining": 0
            }, 403

        return False, {
            "status": "FAILED",
            "error": "Invalid OTP code.",
            "attempts_remaining": attempts_left
        }, 401
