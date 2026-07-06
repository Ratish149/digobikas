from django.db.models import QuerySet

from news.models import News


def get_news_list() -> QuerySet[News]:
    """
    Get all news objects.
    """
    return News.objects.all()
