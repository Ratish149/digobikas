from django.utils.text import slugify

from post.models import Category


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
