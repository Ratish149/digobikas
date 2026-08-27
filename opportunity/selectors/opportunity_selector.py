from django.db.models import QuerySet

from opportunity.models import Opportunity


def get_opportunities_list() -> QuerySet[Opportunity]:
    """
    Get all opportunity objects ordered by created_at descending.
    """
    return Opportunity.objects.all().order_by("-created_at")
