from rest_framework import serializers

from opportunity.models import Opportunity


class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = [
            "id",
            "type",
            "title",
            "description",
            "image",
            "link",
            "apply_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
