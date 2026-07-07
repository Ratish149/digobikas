from django.db.models import QuerySet

from fellowship.models import Fellowship, FellowshipMember


def get_fellowships_list() -> QuerySet[Fellowship]:
    """
    Get all fellowships optimized with prefetch_related for members.
    """
    return Fellowship.objects.prefetch_related("members")


def get_fellowship_members_list() -> QuerySet[FellowshipMember]:
    """
    Get all fellowship members optimized with select_related for fellowship.
    """
    return FellowshipMember.objects.select_related("fellowship")
