import math
from rest_framework import serializers
from .models import Session, Event


class EventInSerializer(serializers.Serializer):
    """
    Matches and validates the envelope shape sent by the extension:
    { type?, event_id, session_id, event_type, timestamp, payload?, device_label? }
    """
    type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    event_id = serializers.CharField(max_length=100)
    session_id = serializers.CharField(max_length=100)
    event_type = serializers.CharField(max_length=50)
    timestamp = serializers.IntegerField(min_value=1)
    payload = serializers.JSONField(required=False, allow_null=True)
    device_label = serializers.CharField(max_length=200, required=False, allow_null=True)

    ALLOWED_EVENT_TYPES = {"MOUSE_BEHAVIOR", "TEST_EVENT"}
    FORBIDDEN_PAYLOAD_KEYS = {"x", "y", "coordinates", "password", "key", "text", "raw"}

    EXPECTED_MOUSE_FEATURES = {
        "movement_count",
        "total_distance",
        "average_velocity",
        "maximum_velocity",
        "velocity_variance",
        "direction_change_count",
        "average_direction_change",
        "path_efficiency",
        "straightness_ratio",
        "movement_duration",
    }

    def validate_event_id(self, value):
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("event_id must not be empty.")
        return stripped

    def validate_session_id(self, value):
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("session_id must not be empty.")
        return stripped

    def validate_event_type(self, value):
        stripped = value.strip()
        if stripped not in self.ALLOWED_EVENT_TYPES:
            raise serializers.ValidationError(
                f"Unsupported event_type '{stripped}'. Must be one of: {', '.join(sorted(self.ALLOWED_EVENT_TYPES))}."
            )
        return stripped

    def validate(self, attrs):
        event_type = attrs.get("event_type")
        payload = attrs.get("payload")

        if event_type == "MOUSE_BEHAVIOR":
            if not isinstance(payload, dict):
                raise serializers.ValidationError({"payload": "Payload must be a JSON object for MOUSE_BEHAVIOR events."})

            # Privacy check: strictly forbid raw coordinates or sensitive inputs
            prohibited_found = set(payload.keys()) & self.FORBIDDEN_PAYLOAD_KEYS
            if prohibited_found:
                raise serializers.ValidationError({
                    "payload": f"Raw coordinates or sensitive fields ({', '.join(sorted(prohibited_found))}) are strictly prohibited."
                })

            # Validate numerical properties of mouse features
            for feature_name, feature_value in payload.items():
                if feature_name in self.EXPECTED_MOUSE_FEATURES:
                    if isinstance(feature_value, bool) or not isinstance(feature_value, (int, float)):
                        raise serializers.ValidationError({
                            "payload": f"Feature '{feature_name}' must be a numeric value."
                        })
                    if not math.isfinite(feature_value):
                        raise serializers.ValidationError({
                            "payload": f"Feature '{feature_name}' must be a finite number."
                        })

            # Range checks on specific kinematic features
            if "movement_count" in payload and payload["movement_count"] < 2:
                raise serializers.ValidationError({"payload": "movement_count must be at least 2."})

            for key in ["total_distance", "movement_duration", "average_velocity", "maximum_velocity", "velocity_variance"]:
                if key in payload and payload[key] < 0:
                    raise serializers.ValidationError({"payload": f"{key} must be non-negative."})

            for ratio_key in ["path_efficiency", "straightness_ratio"]:
                if ratio_key in payload and not (0.0 <= payload[ratio_key] <= 1.0):
                    raise serializers.ValidationError({"payload": f"{ratio_key} must be between 0.0 and 1.0."})

        return attrs

    def create(self, validated_data):
        validated_data.pop("type", None)
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