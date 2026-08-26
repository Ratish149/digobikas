from rest_framework import serializers

from video.models import Video
from video.services.video_service import create_video, update_video


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "video_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        return create_video(**validated_data)

    def update(self, instance, validated_data):
        return update_video(video=instance, **validated_data)
