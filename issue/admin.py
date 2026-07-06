from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Issue


@admin.register(Issue)
class IssueAdmin(ModelAdmin):
    list_display = ["title", "slug", "created_at"]
    search_fields = ["title"]
    prepopulated_fields = {"slug": ("title",)}
