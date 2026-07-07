from django.contrib import admin
from unfold.admin import ModelAdmin

from team.models import TeamMember


@admin.register(TeamMember)
class TeamMemberAdmin(ModelAdmin):
    list_display = ["name", "member_type", "designation", "slug", "created_at"]
    list_filter = ["member_type"]
    search_fields = ["name", "designation"]
    prepopulated_fields = {"slug": ("name",)}
