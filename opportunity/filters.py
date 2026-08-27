import django_filters

from opportunity.models import Opportunity


class OpportunityFilter(django_filters.FilterSet):
    type = django_filters.ChoiceFilter(choices=Opportunity.TYPE_CHOICES)
    search = django_filters.CharFilter(method="filter_search")
    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("apply_by", "apply_by"),
            ("title", "title"),
        )
    )

    class Meta:
        model = Opportunity
        fields = ["type"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(title__icontains=value)
