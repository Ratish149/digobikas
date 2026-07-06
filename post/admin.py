from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Category, Post, Tag


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
    list_display = ["title", "category", "author", "created_at"]
    search_fields = ["title", "content"]
    list_filter = ["category", "created_at"]
    filter_horizontal = ["tags"]
    prepopulated_fields = {"slug": ("title",)}
