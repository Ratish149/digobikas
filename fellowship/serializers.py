from rest_framework import serializers

from fellowship.models import Fellowship, FellowshipMember
from fellowship.services.fellowship_service import (
    create_fellowship,
    create_fellowship_member,
    update_fellowship,
    update_fellowship_member,
)


class FellowshipMemberNestedSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    slug = serializers.SlugField(required=False, read_only=True)

    class Meta:
        model = FellowshipMember
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class FellowshipMemberSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, read_only=True)

    class Meta:
        model = FellowshipMember
        fields = [
            "id",
            "fellowship",
            "slug",
            "name",
            "description",
            "image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        return create_fellowship_member(**validated_data)

    def update(self, instance, validated_data):
        return update_fellowship_member(fellowship_member=instance, **validated_data)


class FellowshipSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, read_only=True)
    members = FellowshipMemberNestedSerializer(many=True, required=False)

    class Meta:
        model = Fellowship
        fields = ["id", "title", "slug", "members", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        members_data = validated_data.pop("members", [])
        return create_fellowship(members_data=members_data, **validated_data)

    def update(self, instance, validated_data):
        return update_fellowship(fellowship=instance, **validated_data)
