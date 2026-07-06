from rest_framework import serializers

from event_report.models import EventReport
from event_report.services.event_report_service import (
    create_event_report,
    update_event_report,
)


class EventReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventReport
        fields = [
            "id",
            "title",
            "slug",
            "thumbnail_image",
            "thumbnail_alt_description",
            "file",
            "content",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        return create_event_report(**validated_data)

    def update(self, instance, validated_data):
        return update_event_report(event_report=instance, **validated_data)
