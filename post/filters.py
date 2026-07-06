import django_filters

from post.models import Category, Post, Tag


class CategoryFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Category
        fields = ["search"]


class TagFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Tag
        fields = ["search"]


class PostsFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name="category__slug", lookup_expr="exact"
    )
    tag = django_filters.CharFilter(field_name="tags__slug", lookup_expr="exact")
    author = django_filters.CharFilter(
        field_name="author__username", lookup_expr="exact"
    )
    search = django_filters.CharFilter(method="filter_search")
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("title", "title"),
        )
    )

    class Meta:
        model = Post
        fields = ["category", "tag", "author"]

    def filter_search(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(Q(title__icontains=value) | Q(content__icontains=value))
