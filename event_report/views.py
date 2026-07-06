from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from digobikas.utils.permissions import IsAdminOrReadOnly
from event_report.filters import EventReportFilter
from event_report.selectors.event_report_selector import get_event_reports_list
from event_report.serializers import EventReportSerializer
from event_report.services.event_report_service import import_event_reports


class EventReportListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = EventReportSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventReportFilter

    def get_queryset(self):
        return get_event_reports_list()


class EventReportRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EventReportSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return get_event_reports_list()


class EventReportImportAPIView(APIView):
    """
    Endpoint to import Event Reports parsed from the local pages.json file.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            result = import_event_reports()
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
