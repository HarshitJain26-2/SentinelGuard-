from django.urls import path
from .views import LoginAttemptView, VerifyOTPView

urlpatterns = [
    path("login/", LoginAttemptView.as_view(), name="security-login"),
    path("verify-otp/", VerifyOTPView.as_view(), name="security-verify-otp"),
]
