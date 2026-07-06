from rest_framework import serializers

from issue.models import Issue
from issue.services.issue_service import create_issue, update_issue


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
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
        return create_issue(**validated_data)

    def update(self, instance, validated_data):
        return update_issue(issue=instance, **validated_data)
