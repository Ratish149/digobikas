from rest_framework import serializers

from team.models import TeamMember
from team.services.team_service import create_team_member, update_team_member


class TeamMemberSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, read_only=True)

    class Meta:
        model = TeamMember
        fields = [
            "id",
            "name",
            "slug",
            "designation",
            "description",
            "image",
            "member_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        return create_team_member(**validated_data)

    def update(self, instance, validated_data):
        return update_team_member(team_member=instance, **validated_data)
