import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.utils import timezone
from detection.models import Session


class SecurityLog(models.Model):
    """
    Audit log capturing adaptive security decisions (ALLOW / OTP / BLOCK)
    for security telemetry and dashboard visualization.
    Zero-PII compliant: strictly prohibits raw coordinates, credentials, or passwords.
    """
    ACTION_CHOICES = [
        ("ALLOW", "Allow"),
        ("OTP", "OTP Required"),
        ("BLOCK", "Block Access"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_logs"
    )
    session_id_raw = models.CharField(max_length=100, blank=True, default="")
    username_attempted = models.CharField(max_length=150, blank=True, default="anonymous")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    risk_score = models.FloatField(help_text="Authoritative server risk score: 0.0 (Human) to 1.0 (Bot)")
    action_taken = models.CharField(max_length=10, choices=ACTION_CHOICES)
    reason = models.TextField(default="Standard behavioral evaluation")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        sess = self.session.session_id if self.session else self.session_id_raw
        return f"[{self.action_taken}] {sess} ({self.username_attempted}) - Risk: {self.risk_score:.4f}"


class OTPChallenge(models.Model):
    """
    Represents a time-bound step-up OTP authentication challenge for medium-risk sessions.
    Stores cryptographically salted hashes instead of plaintext OTPs.
    """
    MAX_ATTEMPTS = 3
    LIFETIME_MINUTES = 5

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="otp_challenges"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="otp_challenges"
    )
    otp_hash = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def set_otp(self, otp_code: str) -> None:
        """Hashes and sets the OTP code using Django's password hashing (PBKDF2)."""
        self.otp_hash = make_password(str(otp_code).strip())

    def check_otp(self, otp_input: str) -> bool:
        """Checks whether the candidate OTP input matches the stored hash."""
        return check_password(str(otp_input).strip(), self.otp_hash)

    def is_valid(self) -> bool:
        """Returns True if the challenge is unverified, unexpired, and under attempt limits."""
        return (
            not self.is_verified
            and timezone.now() < self.expires_at
            and self.attempts < self.MAX_ATTEMPTS
        )

    def __str__(self):
        status_str = "VERIFIED" if self.is_verified else ("EXPIRED" if timezone.now() >= self.expires_at else "ACTIVE")
        return f"OTPChallenge {self.id} for session {self.session.session_id} ({status_str}, attempts={self.attempts})"
