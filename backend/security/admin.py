from django.contrib import admin
from .models import SecurityLog, OTPChallenge


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ("id", "session_id_raw", "username_attempted", "action_taken", "risk_score", "timestamp")
    list_filter = ("action_taken", "timestamp")
    search_fields = ("session_id_raw", "username_attempted", "ip_address")
    ordering = ("-timestamp",)


@admin.register(OTPChallenge)
class OTPChallengeAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "is_verified", "attempts", "created_at", "expires_at")
    list_filter = ("is_verified", "created_at")
    search_fields = ("session__session_id",)
    ordering = ("-created_at",)
