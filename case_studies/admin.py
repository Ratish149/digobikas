from django import forms
from django.contrib import admin
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from .models import CaseStudy


class CaseStudyAdminForm(forms.ModelForm):
    class Meta:
        model = CaseStudy
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


@admin.register(CaseStudy)
class CaseStudyAdmin(ModelAdmin):
    form = CaseStudyAdminForm
    list_display = ["title", "slug", "created_at"]
    search_fields = ["title"]
    prepopulated_fields = {"slug": ("title",)}
