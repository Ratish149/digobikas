import django_filters
from django.db.models import Q

from fellowship.models import Fellowship, FellowshipMember


class FellowshipFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("title", "title"),
        )
    )

    class Meta:
        model = Fellowship
        fields = []

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(title__icontains=value))


class FellowshipMemberFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    fellowship = django_filters.ModelChoiceFilter(
        queryset=Fellowship.objects.all(),
        field_name="fellowship",
    )

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("name", "name"),
        )
    )

    class Meta:
        model = FellowshipMember
        fields = ["fellowship"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )
