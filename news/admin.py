from django import forms
from django.contrib import admin
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from .models import News


class NewsAdminForm(forms.ModelForm):
    class Meta:
        model = News
        fields = [
            "title",
            "slug",
            "thumbnail_image",
            "thumbnail_alt_description",
            "content",
            "url",
            "meta_title",
            "meta_description",
        ]
        widgets = {
            "content": TinyMCE(attrs={"cols": 80, "rows": 70}),
        }


@admin.register(News)
class NewsAdmin(ModelAdmin):
    form = NewsAdminForm
    list_display = ["title", "slug", "created_at"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}

