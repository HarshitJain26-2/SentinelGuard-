from django.db import models


class Session(models.Model):
    """
    One browsing/login session, identified by the session_id
    generated client-side by the extension (SentinelIdentity.generateSessionId()).
    """
    session_id = models.CharField(max_length=100, unique=True)
    device_label = models.CharField(max_length=200, blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.session_id


class Event(models.Model):
    """
    One raw event sent from the extension's content script, matching the
    envelope shape from content.js / service-worker.js:
    { event_id, session_id, event_type, timestamp, ...payload }

    For now (Phase 3 scaffold) this only stores TEST_EVENT entries.
    Once Member 1 adds real mouse/keystroke capture, the same table
    stores those too, with the extra data going in `payload`.
    """
    event_id = models.CharField(max_length=100, unique=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=50)
    client_timestamp = models.BigIntegerField()  # raw epoch ms from the extension
    payload = models.JSONField(blank=True, null=True)  # mouse/keystroke data, once real capture is added
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} ({self.event_id})"


class Score(models.Model):
    """
    ML output for a session: a 0-100 risk score plus which tier it fell into.
    Filled in by Phase 2's model once enough events exist for a session.
    """
    TIER_CHOICES = [
        ("allow", "Allow"),
        ("otp", "OTP Challenge"),
        ("block", "Block"),
    ]

    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name="score")
    risk_score = models.FloatField()  # 0-100, higher = more human-like
    tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    reasons = models.JSONField(blank=True, null=True)  # top contributing signals, for the "why flagged" panel
    scored_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.session_id} -> {self.tier} ({self.risk_score})"


class Decision(models.Model):
    """
    The actual action taken based on a Score (Phase 3's territory).
    Logged separately from Score so the dashboard has a clean audit trail
    even if scoring logic changes later.
    """
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="decisions")
    action_taken = models.CharField(max_length=10, choices=Score.TIER_CHOICES)
    decided_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.session_id}: {self.action_taken}"