import json
import os
import urllib.parse
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.utils.text import slugify

from account.models import CustomUser
from post.models import Category, Post, Tag


def resolve_image_file(attachment):
    """
    Given an attachment dict from attachments.json, find the actual file
    on disk in the flat media/ directory (checking both plain and prefixed names).
    """
    rel_path = attachment.get("postmeta", {}).get("_wp_attached_file")
    if not rel_path:
        url = attachment.get("attachment_url") or attachment.get("guid", "")
        parsed_url = urllib.parse.urlparse(url)
        rel_path = os.path.basename(parsed_url.path)

    if isinstance(rel_path, list):
        rel_path = rel_path[0]

    basename = os.path.basename(rel_path)
    dir_part = os.path.dirname(rel_path)
    prefix = dir_part.replace("/", "_").replace("\\", "_") if dir_part else ""

    media_dir = os.path.join(settings.BASE_DIR, "media")

    # 1. Check plain basename (e.g. Rethinking.jpg)
    path_plain = os.path.join(media_dir, basename)
    if os.path.exists(path_plain):
        return path_plain

    # 2. Check prefixed version (e.g. 2020_11_Rethinking.jpg)
    if prefix:
        path_prefixed = os.path.join(media_dir, f"{prefix}_{basename}")
        if os.path.exists(path_prefixed):
            return path_prefixed

    return None


def create_post(
    *,
    title: str,
    content: str,
    author: CustomUser = None,
    category: Category,
    tags: list[Tag] = None,
    thumbnail=None,
    thumbnail_alt_description: str = None,
    meta_title: str = None,
    meta_description: str = None,
) -> Post:
    with transaction.atomic():
        post = Post(
            title=title,
            content=content,
            author=author,
            category=category,
            thumbnail=thumbnail,
            thumbnail_alt_description=thumbnail_alt_description,
            meta_title=meta_title,
            meta_description=meta_description,
        )
        post.full_clean()
        post.save()

        if tags:
            post.tags.set(tags)

        return post


def update_post(*, post: Post, **data) -> Post:
    tags = data.pop("tags", None)
    with transaction.atomic():
        for field, value in data.items():
            setattr(post, field, value)
        post.full_clean()
        post.save()

        if tags is not None:
            post.tags.set(tags)

        return post


def import_posts_from_json(*, file_path: str | Path, author=None) -> dict:
    """
    Import posts, categories, and tags from a json file, and link their media files.
    """
    attachments_path = os.path.join(settings.BASE_DIR, "attachments.json")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Load attachments to map _thumbnail_id
    attachments_map = {}
    if os.path.exists(attachments_path):
        with open(attachments_path, "r", encoding="utf-8") as f:
            attachments = json.load(f)
            for att in attachments:
                post_id = att.get("post_id")
                if post_id:
                    attachments_map[post_id] = att

    imported_count = 0
    created_posts_count = 0
    updated_posts_count = 0
    created_categories = 0
    created_tags = 0

    with transaction.atomic():
        for item in data:
            title = item.get("title")
            content = item.get("content") or ""

            if not title:
                continue

            categories_data = item.get("categories", [])

            # Find category matching domain == "category"
            category_item = None
            for cat in categories_data:
                if cat.get("domain") == "category":
                    category_item = cat
                    break

            if category_item:
                cat_name = category_item.get("name")
                cat_slug = category_item.get("slug") or slugify(cat_name)
                category, cat_created = Category.objects.get_or_create(
                    slug=cat_slug[:100], defaults={"name": cat_name[:100]}
                )
                if cat_created:
                    created_categories += 1
            else:
                category, cat_created = Category.objects.get_or_create(
                    slug="uncategorized", defaults={"name": "Uncategorized"}
                )
                if cat_created:
                    created_categories += 1

            # Find tags matching domain == "post_tag"
            tags_to_link = []
            for cat in categories_data:
                if cat.get("domain") == "post_tag":
                    tag_name = cat.get("name")
                    tag_slug = cat.get("slug") or slugify(tag_name)
                    tag, tag_created = Tag.objects.get_or_create(
                        slug=tag_slug[:100], defaults={"name": tag_name[:100]}
                    )
                    if tag_created:
                        created_tags += 1
                    tags_to_link.append(tag)

            # Determine post unique identifier
            post_slug = item.get("slug") or slugify(title)
            post_title = title[:100]

            # Look for existing post
            post = Post.objects.filter(slug=post_slug[:100]).first()

            if post:
                # Update existing post if values are missing
                updated = False
                if not post.content and content:
                    post.content = content
                    updated = True
                if not post.category and category:
                    post.category = category
                    updated = True

                # Link thumbnail if missing
                thumbnail_id_str = item.get("postmeta", {}).get("_thumbnail_id")
                if not post.thumbnail and thumbnail_id_str:
                    try:
                        thumbnail_id = int(thumbnail_id_str)
                    except ValueError:
                        thumbnail_id = None

                    if thumbnail_id and thumbnail_id in attachments_map:
                        attachment = attachments_map[thumbnail_id]
                        image_source_path = resolve_image_file(attachment)
                        if image_source_path and os.path.exists(image_source_path):
                            image_filename = os.path.basename(image_source_path)
                            with open(image_source_path, "rb") as img_file:
                                post.thumbnail.save(
                                    image_filename, File(img_file), save=False
                                )
                                alt_text = attachment.get("postmeta", {}).get(
                                    "_wp_attachment_image_alt"
                                )
                                if isinstance(alt_text, list) and alt_text:
                                    alt_text = alt_text[0]
                                if alt_text:
                                    post.thumbnail_alt_description = alt_text
                                updated = True

                if updated:
                    post.save()
                    updated_posts_count += 1

                # Link tags if post doesn't have any linked tags
                if tags_to_link and not post.tags.exists():
                    post.tags.set(tags_to_link)
            else:
                # Create a new post
                post = Post.objects.create(
                    title=post_title,
                    slug=post_slug[:100],
                    content=content,
                    author=None,
                    category=category,
                )

                # Link the post thumbnail if specified in postmeta
                thumbnail_id_str = item.get("postmeta", {}).get("_thumbnail_id")
                if thumbnail_id_str:
                    try:
                        thumbnail_id = int(thumbnail_id_str)
                    except ValueError:
                        thumbnail_id = None

                    if thumbnail_id and thumbnail_id in attachments_map:
                        attachment = attachments_map[thumbnail_id]
                        image_source_path = resolve_image_file(attachment)
                        if image_source_path and os.path.exists(image_source_path):
                            image_filename = os.path.basename(image_source_path)
                            with open(image_source_path, "rb") as img_file:
                                post.thumbnail.save(
                                    image_filename, File(img_file), save=False
                                )
                                alt_text = attachment.get("postmeta", {}).get(
                                    "_wp_attachment_image_alt"
                                )
                                if isinstance(alt_text, list) and alt_text:
                                    alt_text = alt_text[0]
                                if alt_text:
                                    post.thumbnail_alt_description = alt_text
                                post.save()

                if tags_to_link:
                    post.tags.set(tags_to_link)

                created_posts_count += 1

            imported_count += 1

    return {
        "status": "success",
        "processed_posts": imported_count,
        "created_posts": created_posts_count,
        "updated_posts": updated_posts_count,
        "created_categories": created_categories,
        "created_tags": created_tags,
    }


def deduplicate_posts() -> dict:
    """
    Remove duplicate posts having the same slug. Keeps the earliest created one.
    """
    from django.db.models import Count

    # Find all slugs that appear more than once (excluding null/empty slugs)
    duplicate_slugs = (
        Post.objects
        .exclude(slug__isnull=True)
        .exclude(slug="")
        .values("slug")
        .annotate(slug_count=Count("slug"))
        .filter(slug_count__gt=1)
    )

    deleted_count = 0
    details = []

    with transaction.atomic():
        for entry in duplicate_slugs:
            slug = entry["slug"]
            posts = list(Post.objects.filter(slug=slug).order_by("created_at"))
            # Keep the oldest one
            keep_post = posts[0]
            delete_posts = posts[1:]

            deleted_ids = []
            for post in delete_posts:
                deleted_ids.append(post.id)
                post.delete()
                deleted_count += 1

            details.append({
                "slug": slug,
                "kept_id": keep_post.id,
                "deleted_ids": deleted_ids,
            })

    return {
        "status": "success",
        "deleted_count": deleted_count,
        "details": details,
    }
