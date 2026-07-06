from django.utils.text import slugify

from post.models import Tag


def create_tag(*, name: str, slug: str = None) -> Tag:
    if not slug:
        slug = slugify(name)
    tag = Tag(name=name, slug=slug)
    tag.full_clean()
    tag.save()
    return tag


def update_tag(*, tag: Tag, **data) -> Tag:
    if "name" in data and "slug" not in data:
        data["slug"] = slugify(data["name"])
    for field, value in data.items():
        setattr(tag, field, value)
    tag.full_clean()
    tag.save()
    return tag
