from django.db.models import QuerySet

from publication.models import Publication


def get_publications_list() -> QuerySet[Publication]:
    """
    Get all publications objects.
    """
    return Publication.objects.all()
