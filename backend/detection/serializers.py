from rest_framework import serializers
from .models import Session, Event


class EventInSerializer(serializers.Serializer):
    """
    Matches the envelope shape sent by the extension's content script:
    { event_id, session_id, event_type, timestamp, payload? }
    """
    event_id = serializers.CharField(max_length=100)
    session_id = serializers.CharField(max_length=100)
    event_type = serializers.CharField(max_length=50)
    timestamp = serializers.IntegerField()
    payload = serializers.JSONField(required=False, allow_null=True)
    device_label = serializers.CharField(max_length=200, required=False, allow_null=True)

    def create(self, validated_data):
        session, _ = Session.objects.get_or_create(
            session_id=validated_data["session_id"],
            defaults={"device_label": validated_data.get("device_label")}
        )

        event = Event.objects.create(
            event_id=validated_data["event_id"],
            session=session,
            event_type=validated_data["event_type"],
            client_timestamp=validated_data["timestamp"],
            payload=validated_data.get("payload"),
        )
        return event


class EventOutSerializer(serializers.ModelSerializer):
    session_id = serializers.CharField(source="session.session_id")

    class Meta:
        model = Event
        fields = ["event_id", "session_id", "event_type", "client_timestamp", "payload", "received_at"]