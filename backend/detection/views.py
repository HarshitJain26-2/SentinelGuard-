from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import EventInSerializer, EventOutSerializer
from .models import Event


class HealthCheckView(APIView):
    """
    GET /api/health/
    Minimal backend health check endpoint for connectivity verification.
    """

    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class EventCreateView(APIView):
    """
    POST /api/events/
    Receives one event envelope from the extension's content/background script.
    """

    def post(self, request):
        serializer = EventInSerializer(data=request.data)
        if serializer.is_valid():
            # Guard against duplicate event_id (e.g. retry from the extension)
            if Event.objects.filter(event_id=serializer.validated_data["event_id"]).exists():
                return Response({"status": "DUPLICATE"}, status=status.HTTP_200_OK)

            event = serializer.save()
            out = EventOutSerializer(event)
            return Response({"status": "ACK", "event": out.data}, status=status.HTTP_201_CREATED)

        return Response(
            {"status": "REJECTED", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )