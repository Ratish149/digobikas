from django.urls import path

from event_report.views import (
    EventReportImportAPIView,
    EventReportListCreateAPIView,
    EventReportRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "event-reports/",
        EventReportListCreateAPIView.as_view(),
        name="event-report-list-create",
    ),
    path(
        "event-reports/import/",
        EventReportImportAPIView.as_view(),
        name="event-report-import",
    ),
    path(
        "event-reports/<slug:slug>/",
        EventReportRetrieveUpdateDestroyAPIView.as_view(),
        name="event-report-detail",
    ),
]

