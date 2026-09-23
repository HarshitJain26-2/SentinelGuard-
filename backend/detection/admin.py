from django.contrib import admin
from .models import Session, Event, Score, Decision


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "device_label", "started_at")
    search_fields = ("session_id", "device_label")
    ordering = ("-started_at",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "session", "event_type", "client_timestamp", "received_at")
    list_filter = ("event_type",)
    search_fields = ("event_id", "session__session_id")
    ordering = ("-received_at",)


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("session", "risk_score", "tier", "scored_at")
    list_filter = ("tier",)
    ordering = ("-scored_at",)


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ("session", "action_taken", "decided_at")
    list_filter = ("action_taken",)
    ordering = ("-decided_at",)