import django_filters

from contact.models import Contact


class ContactFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("name", "name"),
            ("email", "email"),
        )
    )

    class Meta:
        model = Contact
        fields = []

    def filter_search(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(Q(name__icontains=value) | Q(email__icontains=value))
