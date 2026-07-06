import django_filters

from empowerment_program.models import EmpowermentProgram, EmpowermentProgramCohort


class EmpowermentProgramFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("title", "title"),
        )
    )

    class Meta:
        model = EmpowermentProgram
        fields = []

    def filter_search(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(
            Q(title__icontains=value)
            | Q(content__icontains=value)
        )


class EmpowermentProgramCohortFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    program = django_filters.ModelChoiceFilter(
        queryset=EmpowermentProgram.objects.all(),
        field_name="program",
    )

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("name", "name"),
        )
    )

    class Meta:
        model = EmpowermentProgramCohort
        fields = ["program"]

    def filter_search(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(
            Q(name__icontains=value)
            | Q(image_alt_description__icontains=value)
        )
