from django.utils.text import slugify
from rest_framework import serializers

from .models import Category, Post, Tag
from .services.category_service import create_category, update_category
from .services.post_service import create_post, update_post
from .services.tag_service import create_tag, update_tag


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False)

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]

    def create(self, validated_data):
        return create_category(**validated_data)

    def update(self, instance, validated_data):
        return update_category(category=instance, **validated_data)


class TagSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]

    def create(self, validated_data):
        return create_tag(**validated_data)

    def update(self, instance, validated_data):
        return update_tag(tag=instance, **validated_data)


class TagRelatedField(serializers.RelatedField):
    """
    Custom field that accepts a tag name (string), ID (integer), or dictionary,
    finds the tag if it already exists, or creates a new one and links it.
    """

    def to_internal_value(self, data):
        if isinstance(data, int):
            try:
                return Tag.objects.get(id=data)
            except Tag.DoesNotExist:
                raise serializers.ValidationError(f"Tag with ID {data} does not exist.")

        if isinstance(data, str):
            tag = Tag.objects.filter(name__icontains=data).first()
            if not tag:
                slug = slugify(data)
                tag = Tag.objects.create(name=data, slug=slug)
            return tag

        if isinstance(data, dict):
            name = data.get("name")
            if not name:
                raise serializers.ValidationError("Tag name is required.")
            tag = Tag.objects.filter(name__icontains=name).first()
            if not tag:
                slug = data.get("slug") or slugify(name)
                tag = Tag.objects.create(name=name, slug=slug)
            return tag

        raise serializers.ValidationError(
            "Invalid tag format. Must be an ID, name string, or tag object."
        )

    def to_representation(self, value):
        return TagSerializer(value).data


class PostsSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, read_only=True)
    tags = TagRelatedField(many=True, queryset=Tag.objects.all(), required=False)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "thumbnail",
            "created_at",
            "updated_at",
            "author",
            "category",
            "tags",
            "meta_title",
            "meta_description",
        ]
        read_only_fields = ["slug", "author", "created_at", "updated_at"]

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        return create_post(tags=tags, **validated_data)

    def update(self, instance, validated_data):
        return update_post(post=instance, **validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Use nested representation for read endpoints
        representation["category"] = CategorySerializer(instance.category).data
        representation["tags"] = TagSerializer(instance.tags.all(), many=True).data

        author = instance.author
        if author:
            representation["author"] = {
                "id": author.id,
                "username": author.username,
                "email": author.email,
            }
        else:
            representation["author"] = None

        return representation
