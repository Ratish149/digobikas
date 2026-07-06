from rest_framework import serializers

from publication.models import Publication
from publication.services.publication_service import (
    create_publication,
    update_publication,
)


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = [
            "id",
            "title",
            "slug",
            "thumbnail_image",
            "thumbnail_alt_description",
            "content",
            "file",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        return create_publication(**validated_data)

    def update(self, instance, validated_data):
        return update_publication(publication=instance, **validated_data)
