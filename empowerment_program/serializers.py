from rest_framework import serializers

from empowerment_program.models import (
    CohortVolunteer,
    EmpowermentProgram,
    EmpowermentProgramCohort,
)
from empowerment_program.services.empowerment_service import (
    create_cohort,
    create_cohort_volunteer,
    create_empowerment_program,
    update_cohort,
    update_cohort_volunteer,
    update_empowerment_program,
)


class CohortVolunteerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CohortVolunteer
        fields = [
            "id",
            "cohort",
            "name",
            "image",
            "image_alt_description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        return create_cohort_volunteer(**validated_data)

    def update(self, instance, validated_data):
        return update_cohort_volunteer(cohort_volunteer=instance, **validated_data)


class EmpowermentProgramCohortSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, read_only=True)
    volunteers = CohortVolunteerSerializer(many=True, required=False)

    class Meta:
        model = EmpowermentProgramCohort
        fields = [
            "id",
            "program",
            "name",
            "slug",
            "image",
            "image_alt_description",
            "volunteers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        volunteers_data = validated_data.pop("volunteers", [])
        return create_cohort(volunteers_data=volunteers_data, **validated_data)

    def update(self, instance, validated_data):
        return update_cohort(cohort=instance, **validated_data)


class EmpowermentProgramSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, read_only=True)
    cohorts = EmpowermentProgramCohortSerializer(many=True, read_only=True)

    class Meta:
        model = EmpowermentProgram
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "cohorts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        return create_empowerment_program(**validated_data)

    def update(self, instance, validated_data):
        return update_empowerment_program(program=instance, **validated_data)
