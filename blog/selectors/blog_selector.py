from django.db.models import QuerySet

from blog.models import Blog


def get_blogs_list() -> QuerySet[Blog]:
    """
    Get all blog objects.
    """
    return Blog.objects.all()
