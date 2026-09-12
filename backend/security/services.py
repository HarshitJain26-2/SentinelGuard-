import random
from django.utils import timezone
from datetime import timedelta
from .models import SecurityLog, OTPChallenge

LOW_RISK_THRESHOLD = 0.30
HIGH_RISK_THRESHOLD = 0.70

def process_adaptive_security(username, risk_score, ip_address, reasons=None):
    if risk_score is None:
        risk_score = 0.50
        reasons = (reasons or []) + ["ML Service Unavailable - Defaulting to OTP"]

    if risk_score < LOW_RISK_THRESHOLD:
        action = 'ALLOW'
    elif risk_score >= HIGH_RISK_THRESHOLD:
        action = 'BLOCK'
    else:
        action = 'OTP'

    reason_str = ", ".join(reasons) if reasons else "Standard behavioral evaluation"

    log_entry = SecurityLog.objects.create(
        username_attempted=username,
        ip_address=ip_address,
        risk_score=risk_score,
        action_taken=action,
        reason=reason_str
    )

    return action, log_entry


def create_otp_challenge(user):
    code = f"{random.randint(100000, 999999)}"
    expiry = timezone.now() + timedelta(minutes=5)

    OTPChallenge.objects.filter(user=user, is_verified=False).delete()

    challenge = OTPChallenge.objects.create(
        user=user,
        otp_code=code,
        expires_at=expiry
    )

    print(f"\n[DEMO OTP CODE] User: {user.username} | Code: {code}\n")
    return challenge