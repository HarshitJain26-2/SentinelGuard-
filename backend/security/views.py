"""
SentinelGuard — Adaptive Security API Views

Exposes endpoints for:
1. POST /api/security/login/      -> Evaluates server-authoritative risk score
2. POST /api/security/verify-otp/ -> Verifies step-up OTP challenge
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import process_login_attempt, verify_otp_challenge


class LoginAttemptView(APIView):
    """
    POST /api/security/login/
    Evaluates session login against server-authoritative behavioral risk score.
    Strictly ignores any client-supplied risk_score.
    """

    def post(self, request):
        session_id = request.data.get("session_id")
        username = request.data.get("username", "anonymous")

        if not session_id or not str(session_id).strip():
            return Response(
                {"error": "session_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        client_ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.META.get("REMOTE_ADDR")

        action, result_dict, http_code = process_login_attempt(
            session_id=session_id,
            username=username,
            ip_address=client_ip
        )

        return Response(result_dict, status=http_code)


class VerifyOTPView(APIView):
    """
    POST /api/security/verify-otp/
    Verifies user OTP for an active OTPChallenge.
    """

    def post(self, request):
        challenge_id = request.data.get("challenge_id")
        otp_input = request.data.get("otp")

        if not challenge_id or not str(challenge_id).strip():
            return Response(
                {"error": "challenge_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not otp_input or not str(otp_input).strip():
            return Response(
                {"error": "otp is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        client_ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.META.get("REMOTE_ADDR")

        success, result_dict, http_code = verify_otp_challenge(
            challenge_id=str(challenge_id).strip(),
            otp_input=str(otp_input).strip(),
            ip_address=client_ip
        )

        return Response(result_dict, status=http_code)
