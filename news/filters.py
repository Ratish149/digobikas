import django_filters

from news.models import News


class NewsFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("title", "title"),
        )
    )

    class Meta:
        model = News
        fields = []

    def filter_search(self, queryset, name, value):
        return queryset.filter(title__icontains=value)
