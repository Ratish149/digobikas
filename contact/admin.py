from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Contact


@admin.register(Contact)
class ContactAdmin(ModelAdmin):
    list_display = ["name", "email", "phone", "created_at"]
    search_fields = ["name", "email", "message"]
    readonly_fields = ["created_at", "updated_at"]
