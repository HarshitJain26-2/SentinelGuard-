from django.urls import path
from .views import EventCreateView, HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("events/", EventCreateView.as_view(), name="event-create"),
]