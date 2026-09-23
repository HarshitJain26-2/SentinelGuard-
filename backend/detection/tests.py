import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Session, Event


class HealthCheckTests(APITestCase):
    def test_health_check_returns_ok(self):
        """GET /api/health/ returns status 200 and {'status': 'ok'}."""
        url = reverse("health-check")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})


class EventAPITests(APITestCase):
    def setUp(self):
        self.events_url = reverse("event-create")
        self.valid_mouse_payload = {
            "type": "MOUSE_BEHAVIOR",
            "event_type": "MOUSE_BEHAVIOR",
            "event_id": "evt_test_12345678_0001",
            "session_id": "sess_test_12345678_0001",
            "timestamp": 1727100000000,
            "payload": {
                "movement_count": 25,
                "total_distance": 100.0,
                "movement_duration": 500,
                "average_velocity": 0.2,
                "maximum_velocity": 0.5,
                "velocity_variance": 0.01,
                "direction_change_count": 3,
                "average_direction_change": 0.4,
                "path_efficiency": 0.8,
                "straightness_ratio": 0.9,
            },
        }

    def test_valid_mouse_behavior_event(self):
        """Valid MOUSE_BEHAVIOR event returns HTTP 201 ACK and creates Session and Event records."""
        response = self.client.post(
            self.events_url,
            data=json.dumps(self.valid_mouse_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["status"], "ACK")
        self.assertEqual(data["event"]["event_id"], "evt_test_12345678_0001")
        self.assertEqual(data["event"]["session_id"], "sess_test_12345678_0001")

        # Verify DB records
        self.assertTrue(Session.objects.filter(session_id="sess_test_12345678_0001").exists())
        self.assertTrue(Event.objects.filter(event_id="evt_test_12345678_0001").exists())
        event = Event.objects.get(event_id="evt_test_12345678_0001")
        self.assertEqual(event.event_type, "MOUSE_BEHAVIOR")
        self.assertEqual(event.payload["movement_count"], 25)

    def test_duplicate_event_id(self):
        """Duplicate event_id is safely ignored and returns status DUPLICATE with HTTP 200."""
        # First submission
        res1 = self.client.post(
            self.events_url,
            data=json.dumps(self.valid_mouse_payload),
            content_type="application/json",
        )
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Duplicate submission with same event_id
        res2 = self.client.post(
            self.events_url,
            data=json.dumps(self.valid_mouse_payload),
            content_type="application/json",
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.json(), {"status": "DUPLICATE"})
        self.assertEqual(Event.objects.filter(event_id="evt_test_12345678_0001").count(), 1)

    def test_invalid_session_id(self):
        """Empty or whitespace session_id is rejected with HTTP 400."""
        payload = dict(self.valid_mouse_payload)
        payload["session_id"] = "   "
        payload["event_id"] = "evt_test_invalid_sess"
        response = self.client.post(
            self.events_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["status"], "REJECTED")
        self.assertIn("session_id", response.json()["errors"])

    def test_invalid_event_id(self):
        """Empty or whitespace event_id is rejected with HTTP 400."""
        payload = dict(self.valid_mouse_payload)
        payload["event_id"] = ""
        response = self.client.post(
            self.events_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["status"], "REJECTED")
        self.assertIn("event_id", response.json()["errors"])

    def test_invalid_event_type(self):
        """Unsupported event_type is rejected with HTTP 400."""
        payload = dict(self.valid_mouse_payload)
        payload["event_id"] = "evt_invalid_type"
        payload["event_type"] = "MALICIOUS_INJECTION"
        response = self.client.post(
            self.events_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["status"], "REJECTED")
        self.assertIn("event_type", response.json()["errors"])

    def test_invalid_non_numeric_feature(self):
        """Non-numeric values for expected mouse features are rejected with HTTP 400."""
        payload = json.loads(json.dumps(self.valid_mouse_payload))
        payload["event_id"] = "evt_non_numeric_1"
        payload["payload"]["average_velocity"] = "fast"
        response = self.client.post(
            self.events_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["status"], "REJECTED")
        self.assertIn("payload", response.json()["errors"])

    def test_boolean_feature_rejected_as_non_numeric(self):
        """Boolean values for expected mouse features are rejected with HTTP 400."""
        payload = json.loads(json.dumps(self.valid_mouse_payload))
        payload["event_id"] = "evt_bool_feat"
        payload["payload"]["total_distance"] = True
        response = self.client.post(
            self.events_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["status"], "REJECTED")
        self.assertIn("payload", response.json()["errors"])

    def test_missing_required_event_fields(self):
        """Missing required event fields (session_id, event_id, timestamp) return HTTP 400."""
        incomplete_payload = {
            "event_type": "MOUSE_BEHAVIOR",
            "payload": self.valid_mouse_payload["payload"],
        }
        response = self.client.post(
            self.events_url,
            data=json.dumps(incomplete_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.json()["errors"]
        self.assertIn("event_id", errors)
        self.assertIn("session_id", errors)
        self.assertIn("timestamp", errors)

    def test_raw_coordinates_and_sensitive_keys_prohibited(self):
        """Payload containing raw coordinates or credentials must be rejected for privacy."""
        for forbidden_key in ["x", "y", "coordinates", "password", "key", "text"]:
            payload = json.loads(json.dumps(self.valid_mouse_payload))
            payload["event_id"] = f"evt_forbidden_{forbidden_key}"
            payload["payload"][forbidden_key] = 123
            response = self.client.post(
                self.events_url,
                data=json.dumps(payload),
                content_type="application/json",
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Failed to reject forbidden key: {forbidden_key}",
            )
            self.assertEqual(response.json()["status"], "REJECTED")
            self.assertIn("payload", response.json()["errors"])

    def test_valid_test_event(self):
        """Phase 3 TEST_EVENT remains supported and functional."""
        test_event_payload = {
            "event_id": "evt_test_event_001",
            "session_id": "sess_test_event_001",
            "event_type": "TEST_EVENT",
            "timestamp": 1727100000000,
            "payload": {"info": "handshake test"},
        }
        response = self.client.post(
            self.events_url,
            data=json.dumps(test_event_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["status"], "ACK")
        self.assertTrue(Event.objects.filter(event_id="evt_test_event_001").exists())
