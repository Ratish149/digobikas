from django.db.models import QuerySet

from team.models import TeamMember


def get_team_members_list() -> QuerySet[TeamMember]:
    """
    Get all team members.
    """
    return TeamMember.objects.all()
