from django import forms
from django.contrib import admin
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from .models import Category, Post, Tag


class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            "title",
            "slug",
            "content",
            "thumbnail",
            "thumbnail_alt_description",
            "author",
            "category",
            "tags",
            "meta_title",
            "meta_description",
        ]
        widgets = {
            "content": TinyMCE(attrs={"cols": 80, "rows": 70}),
        }


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostsAdmin(ModelAdmin):
    form = PostAdminForm
    list_display = ["title", "category", "author", "created_at"]
    search_fields = ["title", "content"]
    list_filter = ["category", "created_at"]
    filter_horizontal = ["tags"]
    prepopulated_fields = {"slug": ("title",)}

