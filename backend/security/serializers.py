"""
SentinelGuard — Security Dashboard Serializers

Read-only serializers for dashboard data consumption.
Strictly excludes sensitive fields: ip_address, otp_hash, OTP codes, passwords.
"""

from rest_framework import serializers
from .models import SecurityLog


class SecurityLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for SecurityLog entries displayed on the dashboard.
    Exposes only audit-safe fields. Never exposes ip_address, otp_hash, or secrets.
    """
    session_id = serializers.SerializerMethodField()

    class Meta:
        model = SecurityLog
        fields = [
            "id",
            "session_id",
            "username_attempted",
            "risk_score",
            "action_taken",
            "reason",
            "timestamp",
        ]
        read_only_fields = fields

    def get_session_id(self, obj):
        """Returns the raw session identifier string."""
        if obj.session:
            return obj.session.session_id
        return obj.session_id_raw or ""
