import django_filters

from team.models import TeamMember


class TeamMemberFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    member_type = django_filters.ChoiceFilter(
        choices=TeamMember.MEMBER_TYPE_CHOICE, field_name="member_type"
    )

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("name", "name"),
        )
    )

    class Meta:
        model = TeamMember
        fields = ["member_type"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(name__icontains=value)
