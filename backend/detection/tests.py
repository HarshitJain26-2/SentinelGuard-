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


from unittest.mock import patch
from django.test import TestCase
from .models import Score
from ml.features import FEATURE_NAMES, extract_features_from_payload, FeatureExtractionError
from ml.dataset import generate_synthetic_data
from ml.train_model import train_and_evaluate
from ml.inference import get_model, predict_risk


class MLPipelineTests(TestCase):
    """
    Automated tests for ML Dataset, Feature Extraction, Training, and Inference.
    """

    def setUp(self):
        self.sample_payload = {
            "movement_count": 24,
            "total_distance": 185.5,
            "movement_duration": 650.0,
            "average_velocity": 0.285,
            "maximum_velocity": 0.55,
            "velocity_variance": 0.032,
            "direction_change_count": 4,
            "average_direction_change": 0.38,
            "path_efficiency": 0.82,
            "straightness_ratio": 0.88,
        }

    def test_1_synthetic_dataset_generation(self):
        """Synthetic dataset generator creates balanced, valid dataset with 10 features."""
        df = generate_synthetic_data(n_samples=200, random_state=42)
        self.assertEqual(len(df), 200)
        expected_cols = FEATURE_NAMES + ["label"]
        self.assertListEqual(list(df.columns), expected_cols)
        self.assertEqual((df["label"] == 0).sum(), 100)
        self.assertEqual((df["label"] == 1).sum(), 100)
        self.assertFalse(df.isna().any().any())

    def test_2_feature_extraction(self):
        """Feature extraction correctly extracts 10 numeric values from payload."""
        features = extract_features_from_payload(self.sample_payload)
        self.assertEqual(len(features), 10)
        self.assertTrue(all(isinstance(v, float) for v in features))
        self.assertAlmostEqual(features[0], 24.0)
        self.assertAlmostEqual(features[1], 185.5)

    def test_3_feature_ordering(self):
        """Feature extraction maintains strict FEATURE_NAMES order regardless of dict key order."""
        reversed_payload = {k: self.sample_payload[k] for k in reversed(list(self.sample_payload.keys()))}
        extracted = extract_features_from_payload(reversed_payload)
        expected = [float(self.sample_payload[k]) for k in FEATURE_NAMES]
        self.assertListEqual(extracted, expected)

    def test_4_model_training(self):
        """Model training executes and produces valid classification metrics."""
        metrics = train_and_evaluate(save_model=False, n_samples=200, random_state=42)
        self.assertIn("accuracy", metrics)
        self.assertIn("roc_auc", metrics)
        self.assertGreater(metrics["accuracy"], 0.70)
        self.assertGreater(metrics["roc_auc"], 0.70)
        self.assertIn("confusion_matrix", metrics)

    def test_5_model_loading(self):
        """Model artifact can be loaded and has expected classifier attributes."""
        model = get_model()
        self.assertIsNotNone(model)
        self.assertTrue(hasattr(model, "predict_proba"))
        self.assertEqual(model.n_features_in_, 10)

    def test_6_risk_score_range(self):
        """Inference produces risk score strictly within [0.0, 1.0]."""
        features = extract_features_from_payload(self.sample_payload)
        score = predict_risk(features)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_7_missing_feature_rejection(self):
        """Feature extraction rejects payloads missing required features."""
        incomplete = dict(self.sample_payload)
        del incomplete["total_distance"]
        with self.assertRaises(FeatureExtractionError) as ctx:
            extract_features_from_payload(incomplete)
        self.assertIn("total_distance", str(ctx.exception))


class MLScoringIntegrationTests(APITestCase):
    """
    Automated tests for Django Event Ingestion -> ML Scoring -> Score Persistence.
    """

    def setUp(self):
        self.events_url = reverse("event-create")
        self.valid_mouse_event = {
            "type": "MOUSE_BEHAVIOR",
            "event_type": "MOUSE_BEHAVIOR",
            "event_id": "evt_ml_test_001",
            "session_id": "sess_ml_test_001",
            "timestamp": 1727101000000,
            "payload": {
                "movement_count": 25,
                "total_distance": 140.0,
                "movement_duration": 600,
                "average_velocity": 0.233,
                "maximum_velocity": 0.52,
                "velocity_variance": 0.028,
                "direction_change_count": 4,
                "average_direction_change": 0.36,
                "path_efficiency": 0.81,
                "straightness_ratio": 0.87,
            },
        }

    def test_8_valid_mouse_behavior_gets_scored(self):
        """Valid MOUSE_BEHAVIOR ingestion automatically calculates risk score in API response."""
        response = self.client.post(
            self.events_url,
            data=json.dumps(self.valid_mouse_event),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["status"], "ACK")
        self.assertIn("risk_score", data)
        self.assertGreaterEqual(data["risk_score"], 0.0)
        self.assertLessEqual(data["risk_score"], 1.0)

    def test_9_score_is_persisted_in_database(self):
        """Score record is persisted in SQLite with linked session, event, and explainability reasons."""
        response = self.client.post(
            self.events_url,
            data=json.dumps(self.valid_mouse_event),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        score = Score.objects.get(session__session_id="sess_ml_test_001")
        self.assertIsNotNone(score)
        self.assertEqual(score.event.event_id, "evt_ml_test_001")
        self.assertGreaterEqual(score.risk_score, 0.0)
        self.assertLessEqual(score.risk_score, 1.0)
        self.assertIsInstance(score.reasons, dict)

    def test_10_duplicate_event_does_not_create_duplicate_scores(self):
        """Duplicate event submission returns DUPLICATE and does not create duplicate Score records."""
        res1 = self.client.post(
            self.events_url,
            data=json.dumps(self.valid_mouse_event),
            content_type="application/json",
        )
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Resend exact same event
        res2 = self.client.post(
            self.events_url,
            data=json.dumps(self.valid_mouse_event),
            content_type="application/json",
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.json()["status"], "DUPLICATE")

        self.assertEqual(Score.objects.filter(session__session_id="sess_ml_test_001").count(), 1)

    def test_11_non_mouse_event_not_scored(self):
        """TEST_EVENT is ingested into Event table but does not create a Score row."""
        test_event = {
            "event_id": "evt_test_no_score",
            "session_id": "sess_test_no_score",
            "event_type": "TEST_EVENT",
            "timestamp": 1727101000000,
            "payload": {"info": "handshake"},
        }
        response = self.client.post(
            self.events_url,
            data=json.dumps(test_event),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("risk_score", response.json())
        self.assertFalse(Score.objects.filter(session__session_id="sess_test_no_score").exists())

    def test_12_ml_failure_does_not_destroy_original_event(self):
        """ML inference failure logs error but preserves Event record and returns successful ACK."""
        with patch("detection.ml_scoring.predict_risk", side_effect=RuntimeError("Simulated ML engine crash")):
            fail_event = dict(self.valid_mouse_event)
            fail_event["event_id"] = "evt_ml_fail_safe"
            fail_event["session_id"] = "sess_ml_fail_safe"

            response = self.client.post(
                self.events_url,
                data=json.dumps(fail_event),
                content_type="application/json",
            )
            # Ingestion must still succeed
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.json()["status"], "ACK")

            # Event must exist in database
            self.assertTrue(Event.objects.filter(event_id="evt_ml_fail_safe").exists())

            # Score was not created due to failure
            self.assertFalse(Score.objects.filter(session__session_id="sess_ml_fail_safe").exists())

