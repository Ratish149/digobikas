from django.db.models import QuerySet

from post.models import Post


def get_posts_list() -> QuerySet:
    """
    Get a queryset of posts optimized to prevent N+1 queries.
    """
    return Post.objects.select_related("author", "category").prefetch_related("tags")
