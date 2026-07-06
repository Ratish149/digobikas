from rest_framework import serializers

from case_studies.models import CaseStudy
from case_studies.services.case_study_service import (
    create_case_study,
    update_case_study,
)


class CaseStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStudy
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
        return create_case_study(**validated_data)

    def update(self, instance, validated_data):
        return update_case_study(case_study=instance, **validated_data)
