from rest_framework import serializers

from blog.models import Blog
from blog.services.blog_service import create_blog, update_blog


class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "slug",
            "thumbnail_image",
            "thumbnail_alt_description",
            "file",
            "content",
            "url",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        return create_blog(**validated_data)

    def update(self, instance, validated_data):
        return update_blog(blog=instance, **validated_data)
