from rest_framework import serializers

from news.models import News
from news.services.news_service import create_news, update_news


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = [
            "id",
            "title",
            "slug",
            "thumbnail_image",
            "thumbnail_alt_description",
            "content",
            "url",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        return create_news(**validated_data)

    def update(self, instance, validated_data):
        return update_news(news=instance, **validated_data)
