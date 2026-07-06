from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Blog


@admin.register(Blog)
class BlogAdmin(ModelAdmin):
    list_display = ["title", "slug", "created_at"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}

