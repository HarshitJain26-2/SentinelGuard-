from django.urls import path
from .views import LoginAttemptView, VerifyOTPView

urlpatterns = [
    path('login/', LoginAttemptView.as_view(), name='api_login'),
    path('verify-otp/', VerifyOTPView.as_view(), name='api_verify_otp'),
]