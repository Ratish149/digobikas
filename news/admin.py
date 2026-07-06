from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import News


@admin.register(News)
class NewsAdmin(ModelAdmin):
    list_display = ["title", "slug", "created_at"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}

