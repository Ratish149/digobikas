from django import forms
from django.contrib import admin
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from event_report.models import EventReport


class EventReportAdminForm(forms.ModelForm):
    class Meta:
        model = EventReport
        fields = [
            "title",
            "slug",
            "thumbnail_image",
            "thumbnail_alt_description",
            "file",
            "content",
            "meta_title",
            "meta_description",
        ]
        widgets = {
            "content": TinyMCE(attrs={"cols": 80, "rows": 70}),
        }


@admin.register(EventReport)
class EventReportAdmin(ModelAdmin):
    form = EventReportAdminForm
    list_display = ["title", "slug", "created_at", "updated_at"]
    search_fields = ["title", "thumbnail_alt_description", "file_alt_description"]
    list_filter = ["created_at"]
    prepopulated_fields = {"slug": ("title",)}
