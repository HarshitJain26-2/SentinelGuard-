from django.urls import path
from .views import LoginAttemptView, VerifyOTPView, DashboardStatsView, SecurityLogsView

urlpatterns = [
    path("login/", LoginAttemptView.as_view(), name="security-login"),
    path("verify-otp/", VerifyOTPView.as_view(), name="security-verify-otp"),
    path("stats/", DashboardStatsView.as_view(), name="security-stats"),
    path("logs/", SecurityLogsView.as_view(), name="security-logs"),
]
