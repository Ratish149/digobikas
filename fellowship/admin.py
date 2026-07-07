from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from fellowship.models import Fellowship, FellowshipMember


class FellowshipMemberInline(TabularInline):
    model = FellowshipMember
    extra = 1
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Fellowship)
class FellowshipAdmin(ModelAdmin):
    list_display = ["title", "slug", "created_at"]
    search_fields = ["title"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [FellowshipMemberInline]


@admin.register(FellowshipMember)
class FellowshipMemberAdmin(ModelAdmin):
    list_display = ["name", "fellowship", "slug", "created_at"]
    search_fields = ["name", "fellowship__title"]
    prepopulated_fields = {"slug": ("name",)}
