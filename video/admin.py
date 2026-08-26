from django.contrib import admin
from unfold.admin import ModelAdmin

from video.models import Video


@admin.register(Video)
class VideoAdmin(ModelAdmin):
    list_display = ["title", "video_url", "created_at", "updated_at"]
    search_fields = ["title"]
    list_filter = ["created_at"]
