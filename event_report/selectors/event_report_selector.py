from django.db.models import QuerySet

from event_report.models import EventReport


def get_event_reports_list() -> QuerySet:
    """
    Get a queryset of event reports.
    """
    return EventReport.objects.all()
