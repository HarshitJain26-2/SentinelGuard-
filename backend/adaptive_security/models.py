import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SecurityLog(models.Model):
    ACTION_CHOICES = [
        ('ALLOW', 'Allow'),
        ('OTP', 'OTP Required'),
        ('BLOCK', 'Block Access'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username_attempted = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    risk_score = models.FloatField(help_text="0.0 (Human) to 1.0 (Bot)")
    action_taken = models.CharField(max_length=10, choices=ACTION_CHOICES)
    reason = models.TextField(default="Behavioral Evaluation")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.username_attempted} - {self.action_taken} ({self.risk_score})"


class OTPChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_challenges")
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    def is_valid(self):
        return timezone.now() < self.expires_at and not self.is_verified and self.attempts < 3
