from django.contrib import admin
from unfold.admin import ModelAdmin

from event_report.models import EventReport


@admin.register(EventReport)
class EventReportAdmin(ModelAdmin):
    list_display = ["title", "slug", "created_at", "updated_at"]
    search_fields = ["title", "thumbnail_alt_description", "file_alt_description"]
    list_filter = ["created_at"]
    prepopulated_fields = {"slug": ("title",)}
