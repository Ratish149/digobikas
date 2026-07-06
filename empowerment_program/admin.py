from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import CohortVolunteer, EmpowermentProgram, EmpowermentProgramCohort


class CohortVolunteerInline(TabularInline):
    model = CohortVolunteer
    extra = 1


class EmpowermentProgramCohortInline(TabularInline):
    model = EmpowermentProgramCohort
    extra = 1
    prepopulated_fields = {"slug": ("name",)}


@admin.register(EmpowermentProgram)
class EmpowermentProgramAdmin(ModelAdmin):
    list_display = ["title", "slug", "created_at"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [EmpowermentProgramCohortInline]


@admin.register(EmpowermentProgramCohort)
class EmpowermentProgramCohortAdmin(ModelAdmin):
    list_display = ["name", "program", "slug", "created_at"]
    search_fields = ["name", "program__title"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CohortVolunteerInline]


@admin.register(CohortVolunteer)
class CohortVolunteerAdmin(ModelAdmin):
    list_display = ["name", "cohort", "created_at"]
    search_fields = ["name", "cohort__name"]

