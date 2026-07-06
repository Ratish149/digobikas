import django_filters

from blog.models import Blog


class BlogFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("title", "title"),
        )
    )

    class Meta:
        model = Blog
        fields = []

    def filter_search(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(
            Q(title__icontains=value)
            | Q(content__icontains=value)
            | Q(thumbnail_alt_description__icontains=value)
        )
