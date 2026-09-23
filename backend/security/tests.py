import json
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase

from detection.models import Session, Score, Decision
from security.models import SecurityLog, OTPChallenge
from security.services import (
    evaluate_policy_action,
    create_otp_challenge,
    process_login_attempt,
    verify_otp_challenge,
    LOW_RISK_THRESHOLD,
    HIGH_RISK_THRESHOLD,
    FALLBACK_RISK_SCORE,
)


class PolicyBoundaryTests(TestCase):
    """
    Unit tests verifying exact boundary thresholds for adaptive security policy.
    Thresholds:
      risk_score < 0.30        -> ALLOW
      0.30 <= risk_score < 0.70 -> OTP
      risk_score >= 0.70       -> BLOCK
    """

    def test_1_risk_below_0_30_is_allow(self):
        self.assertEqual(evaluate_policy_action(0.15), "ALLOW")
        self.assertEqual(evaluate_policy_action(0.299999), "ALLOW")

    def test_2_risk_exactly_0_30_is_otp(self):
        self.assertEqual(evaluate_policy_action(0.30), "OTP")

    def test_3_risk_between_0_30_and_0_70_is_otp(self):
        self.assertEqual(evaluate_policy_action(0.45), "OTP")
        self.assertEqual(evaluate_policy_action(0.699999), "OTP")

    def test_4_risk_exactly_0_70_is_block(self):
        self.assertEqual(evaluate_policy_action(0.70), "BLOCK")

    def test_5_risk_above_0_70_is_block(self):
        self.assertEqual(evaluate_policy_action(0.85), "BLOCK")
        self.assertEqual(evaluate_policy_action(0.9999), "BLOCK")

    def test_6_risk_exactly_0_is_allow(self):
        self.assertEqual(evaluate_policy_action(0.0), "ALLOW")

    def test_7_risk_exactly_1_is_block(self):
        self.assertEqual(evaluate_policy_action(1.0), "BLOCK")


class SecurityAPITests(APITestCase):
    """
    Integration tests for /api/security/login/ and /api/security/verify-otp/.
    """

    def setUp(self):
        self.login_url = reverse("security-login")
        self.verify_url = reverse("security-verify-otp")

        # Create test sessions
        self.low_risk_session = Session.objects.create(session_id="sess_test_low_risk")
        self.low_score = Score.objects.create(
            session=self.low_risk_session,
            risk_score=0.10,
            reasons={"path_efficiency": "Nominal human behavior"}
        )

        self.medium_risk_session = Session.objects.create(session_id="sess_test_med_risk")
        self.med_score = Score.objects.create(
            session=self.medium_risk_session,
            risk_score=0.45,
            reasons={"velocity_variance": "Slightly low variance"}
        )

        self.high_risk_session = Session.objects.create(session_id="sess_test_high_risk")
        self.high_score = Score.objects.create(
            session=self.high_risk_session,
            risk_score=0.92,
            reasons={"path_efficiency": "Linear script automation"}
        )

        self.no_score_session = Session.objects.create(session_id="sess_test_no_score")

    # --------------------------------------------------------
    # Critical Security Tests (Client Spoofing Rejection)
    # --------------------------------------------------------
    def test_8_client_provided_risk_score_is_ignored_and_db_authoritative_block(self):
        """
        CRITICAL SECURITY TEST:
        Client sends risk_score=0.0 attempting to spoof a human session.
        Server database has risk_score=0.92 (bot).
        Server MUST return HTTP 403 BLOCK. Client score MUST have zero influence.
        """
        payload = {
            "session_id": "sess_test_high_risk",
            "risk_score": 0.0,
            "tier": "allow",
            "action": "ALLOW",
            "is_bot": False
        }
        response = self.client.post(self.login_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertEqual(data["action"], "BLOCK")
        self.assertAlmostEqual(data["risk_score"], 0.92)

    def test_9_client_provided_risk_score_is_ignored_and_db_authoritative_allow(self):
        """
        Client sends risk_score=0.99 but database has risk_score=0.10.
        Server returns HTTP 200 ALLOW based on authoritative database score.
        """
        payload = {
            "session_id": "sess_test_low_risk",
            "risk_score": 0.99
        }
        response = self.client.post(self.login_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["action"], "ALLOW")
        self.assertAlmostEqual(data["risk_score"], 0.10)

    def test_10_no_score_fallback_to_neutral_otp(self):
        """
        When session exists without a Score, server defaults safely to neutral 0.50 risk and OTP.
        Does NOT create a fake ML score in detection_score.
        """
        payload = {"session_id": "sess_test_no_score"}
        response = self.client.post(self.login_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        data = response.json()
        self.assertEqual(data["action"], "OTP")
        self.assertAlmostEqual(data["risk_score"], 0.50)
        self.assertIn("challenge_id", data)

        # Confirm no fake Score row was persisted in detection_score
        self.assertFalse(Score.objects.filter(session=self.no_score_session).exists())

    # --------------------------------------------------------
    # OTP Lifecycle Tests
    # --------------------------------------------------------
    def test_11_otp_creation(self):
        """Medium risk session generates a valid OTPChallenge with expiration and hash."""
        payload = {"session_id": "sess_test_med_risk"}
        response = self.client.post(self.login_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        data = response.json()
        self.assertEqual(data["action"], "OTP")
        self.assertIn("challenge_id", data)

        challenge = OTPChallenge.objects.get(id=data["challenge_id"])
        self.assertIsNotNone(challenge)
        self.assertFalse(challenge.is_verified)
        self.assertEqual(challenge.attempts, 0)
        self.assertGreater(challenge.expires_at, timezone.now())
        # Confirm hash is stored using Django's password hashing (PBKDF2 format)
        self.assertTrue(challenge.otp_hash.startswith("pbkdf2_sha256$"))

    def test_12_otp_expiration(self):
        """Expired OTPChallenge is rejected upon verification."""
        challenge, code = create_otp_challenge(session=self.medium_risk_session)
        # Fast-forward challenge past expiration (5 minutes + 1 second)
        challenge.expires_at = timezone.now() - timedelta(seconds=1)
        challenge.save()

        verify_payload = {
            "challenge_id": str(challenge.id),
            "otp": code
        }
        response = self.client.post(self.verify_url, data=verify_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", response.json()["error"].lower())

    def test_13_wrong_otp_increments_attempts(self):
        """Submitting incorrect OTP increments attempts and returns remaining count."""
        challenge, code = create_otp_challenge(session=self.medium_risk_session)
        verify_payload = {
            "challenge_id": str(challenge.id),
            "otp": "000000" if code != "000000" else "111111"
        }
        response = self.client.post(self.verify_url, data=verify_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertEqual(data["status"], "FAILED")
        self.assertEqual(data["attempts_remaining"], 2)

        challenge.refresh_from_db()
        self.assertEqual(challenge.attempts, 1)

    def test_14_third_failed_attempt_locks_challenge(self):
        """Three consecutive incorrect OTP attempts permanently lock challenge (HTTP 403)."""
        challenge, code = create_otp_challenge(session=self.medium_risk_session)
        wrong_code = "999999" if code != "999999" else "888888"

        # Attempt 1
        self.client.post(self.verify_url, data={"challenge_id": str(challenge.id), "otp": wrong_code}, format="json")
        # Attempt 2
        self.client.post(self.verify_url, data={"challenge_id": str(challenge.id), "otp": wrong_code}, format="json")
        # Attempt 3 (Lockout)
        res3 = self.client.post(self.verify_url, data={"challenge_id": str(challenge.id), "otp": wrong_code}, format="json")

        self.assertEqual(res3.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res3.json()["attempts_remaining"], 0)

        challenge.refresh_from_db()
        self.assertEqual(challenge.attempts, 3)
        self.assertFalse(challenge.is_valid())

        # Further attempts are also blocked
        res4 = self.client.post(self.verify_url, data={"challenge_id": str(challenge.id), "otp": code}, format="json")
        self.assertEqual(res4.status_code, status.HTTP_403_FORBIDDEN)

    def test_15_successful_otp_verification(self):
        """Correct OTP code verifies challenge and returns HTTP 200 ALLOW."""
        challenge, code = create_otp_challenge(session=self.medium_risk_session)
        verify_payload = {
            "challenge_id": str(challenge.id),
            "otp": code
        }
        response = self.client.post(self.verify_url, data=verify_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["action"], "ALLOW")

        challenge.refresh_from_db()
        self.assertTrue(challenge.is_verified)

    def test_16_reused_otp_rejected(self):
        """Verified OTPChallenge cannot be reused."""
        challenge, code = create_otp_challenge(session=self.medium_risk_session)
        # First verification succeeds
        self.client.post(self.verify_url, data={"challenge_id": str(challenge.id), "otp": code}, format="json")

        # Second verification fails
        response = self.client.post(self.verify_url, data={"challenge_id": str(challenge.id), "otp": code}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been verified", response.json()["error"].lower())

    def test_17_expired_otp_rejected_even_with_correct_code(self):
        """Correct OTP submitted after expiration timestamp is rejected."""
        challenge, code = create_otp_challenge(session=self.medium_risk_session)
        challenge.expires_at = timezone.now() - timedelta(minutes=1)
        challenge.save()

        response = self.client.post(self.verify_url, data={"challenge_id": str(challenge.id), "otp": code}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", response.json()["error"].lower())

    # --------------------------------------------------------
    # Security Audit Logging & Decision Model Tests
    # --------------------------------------------------------
    def test_18_security_log_created_on_login_and_verify(self):
        """SecurityLog records decisions and reasons for auditability."""
        initial_logs_count = SecurityLog.objects.count()

        # Login attempt
        self.client.post(self.login_url, data={"session_id": "sess_test_low_risk"}, format="json")
        self.assertEqual(SecurityLog.objects.count(), initial_logs_count + 1)

        latest_log = SecurityLog.objects.first()
        self.assertEqual(latest_log.action_taken, "ALLOW")
        self.assertAlmostEqual(latest_log.risk_score, 0.10)
        self.assertEqual(latest_log.session, self.low_risk_session)

        # Decision model was also updated
        self.assertTrue(Decision.objects.filter(session=self.low_risk_session, action_taken="allow").exists())

    def test_19_duplicate_login_attempts_handled_sensibly(self):
        """Subsequent login attempts re-evaluate latest authoritative state safely."""
        res1 = self.client.post(self.login_url, data={"session_id": "sess_test_low_risk"}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        res2 = self.client.post(self.login_url, data={"session_id": "sess_test_low_risk"}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

    def test_20_invalid_and_empty_session_id_handled_safely(self):
        """Empty or missing session_id returns HTTP 400 Bad Request."""
        res1 = self.client.post(self.login_url, data={}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        res2 = self.client.post(self.login_url, data={"session_id": "   "}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_21_missing_fields_on_verify_handled_safely(self):
        """Missing challenge_id or otp on verify-otp returns HTTP 400."""
        res1 = self.client.post(self.verify_url, data={"otp": "123456"}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        res2 = self.client.post(self.verify_url, data={"challenge_id": "some-id"}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_22_otp_success_uses_authoritative_risk_score(self):
        """
        OTP verification success must use the authoritative Score.risk_score in SecurityLog,
        not a hardcoded 0.0. Proves: session Score = 0.55, OTP succeeds,
        resulting SecurityLog risk_score = 0.55.
        """
        # Create session with known risk_score = 0.55
        otp_session = Session.objects.create(session_id="sess_otp_risk_test")
        Score.objects.create(
            session=otp_session,
            risk_score=0.55,
            reasons={"velocity_variance": "Slightly anomalous"}
        )

        # Create OTP challenge and verify it
        challenge, code = create_otp_challenge(session=otp_session)
        response = self.client.post(
            self.verify_url,
            data={"challenge_id": str(challenge.id), "otp": code},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "SUCCESS")

        # The SecurityLog for OTP success must contain risk_score=0.55, NOT 0.0
        otp_success_log = SecurityLog.objects.filter(
            session=otp_session,
            action_taken="ALLOW",
            reason="Step-up OTP challenge verified successfully"
        ).first()
        self.assertIsNotNone(otp_success_log)
        self.assertAlmostEqual(otp_success_log.risk_score, 0.55)
