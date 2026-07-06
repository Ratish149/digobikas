from django.db.models import QuerySet

from issue.models import Issue


def get_issues_list() -> QuerySet[Issue]:
    """
    Get a queryset of all issues.
    """
    return Issue.objects.all()
