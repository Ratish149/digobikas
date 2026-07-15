from django import forms
from django.contrib import admin
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from .models import Blog


class BlogAdminForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = [
            "title",
            "slug",
            "thumbnail_image",
            "thumbnail_alt_description",
            "file",
            "content",
            "url",
            "meta_title",
            "meta_description",
        ]
        widgets = {
            "content": TinyMCE(attrs={"cols": 80, "rows": 70}),
        }


@admin.register(Blog)
class BlogAdmin(ModelAdmin):
    form = BlogAdminForm
    list_display = ["title", "slug", "created_at"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}
