from django.db import transaction
from django.utils.text import slugify

from post.models import Category, Post


def create_category(*, name: str, slug: str = None) -> Category:
    if not slug:
        slug = slugify(name)
    category = Category(name=name, slug=slug)
    category.full_clean()
    category.save()
    return category


def update_category(*, category: Category, **data) -> Category:
    if "name" in data and "slug" not in data:
        data["slug"] = slugify(data["name"])
    for field, value in data.items():
        setattr(category, field, value)
    category.full_clean()
    category.save()
    return category


def remove_uncategorized_category() -> dict:
    """
    Finds all 'Uncategorized' categories, sets category=None on all associated posts,
    and deletes the 'Uncategorized' category records.
    """
    with transaction.atomic():
        uncategorized_qs = Category.objects.filter(name__iexact="uncategorized")
        if not uncategorized_qs.exists():
            return {"status": "success", "updated_posts": 0, "deleted_categories": 0}

        posts_qs = Post.objects.filter(category__in=uncategorized_qs)
        updated_posts_count = posts_qs.update(category=None)
        deleted_categories_count, _ = uncategorized_qs.delete()

        return {
            "status": "success",
            "updated_posts": updated_posts_count,
            "deleted_categories": deleted_categories_count,
        }
