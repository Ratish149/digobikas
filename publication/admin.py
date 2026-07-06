from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Publication


@admin.register(Publication)
class PublicationAdmin(ModelAdmin):
    list_display = ["title", "slug", "created_at"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}

