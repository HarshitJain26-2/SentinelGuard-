from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

from .services import process_adaptive_security, create_otp_challenge
from .models import OTPChallenge, SecurityLog

class LoginAttemptView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        
        try:
            risk_score = float(request.data.get("risk_score", 0.0))
        except (ValueError, TypeError):
            risk_score = 0.50

        reasons = request.data.get("reasons", [])

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        client_ip = request.META.get('REMOTE_ADDR')
        action, _ = process_adaptive_security(username, risk_score, client_ip, reasons)

        if action == 'ALLOW':
            login(request, user)
            return Response({"action": "ALLOW", "message": "Login granted."})

        elif action == 'OTP':
            create_otp_challenge(user)
            return Response({
                "action": "OTP",
                "message": "OTP step-up authentication required.",
                "username": username
            }, status=status.HTTP_202_ACCEPTED)

        elif action == 'BLOCK':
            return Response({
                "action": "BLOCK",
                "message": "Access blocked due to bot detection."
            }, status=status.HTTP_403_FORBIDDEN)


class VerifyOTPView(APIView):
    def post(self, request):
        username = request.data.get("username")
        otp_input = str(request.data.get("otp", "")).strip()

        try:
            challenge = OTPChallenge.objects.filter(
                user__username=username, 
                is_verified=False
            ).latest('created_at')
        except OTPChallenge.DoesNotExist:
            return Response({"error": "No active OTP request."}, status=status.HTTP_400_BAD_REQUEST)

        if not challenge.is_valid():
            return Response({"error": "OTP expired or max attempts reached."}, status=status.HTTP_400_BAD_REQUEST)

        if challenge.otp_code == otp_input:
            challenge.is_verified = True
            challenge.save()
            return Response({"status": "SUCCESS", "message": "OTP verified successfully."})
        else:
            challenge.attempts += 1
            challenge.save()
            return Response({"error": "Invalid OTP code."}, status=status.HTTP_401_UNAUTHORIZED)