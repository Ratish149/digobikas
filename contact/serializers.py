from rest_framework import serializers

from contact.models import Contact
from contact.services.contact_service import create_contact, update_contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        return create_contact(**validated_data)

    def update(self, instance, validated_data):
        return update_contact(contact=instance, **validated_data)
