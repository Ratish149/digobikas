from django import forms
from django.contrib import admin
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from opportunity.models import Opportunity


class OpportunityAdminForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = [
            "type",
            "title",
            "description",
            "image",
            "link",
            "apply_by",
        ]
        widgets = {
            "description": TinyMCE(attrs={"cols": 80, "rows": 70}),
        }


@admin.register(Opportunity)
class OpportunityAdmin(ModelAdmin):
    form = OpportunityAdminForm
    list_display = ["title", "type", "apply_by", "created_at"]
    list_filter = ["type"]
    search_fields = ["title", "description"]
