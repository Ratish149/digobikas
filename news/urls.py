from django.urls import path

from news.views import (
    NewsImportAPIView,
    NewsListCreateAPIView,
    NewsRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "news/",
        NewsListCreateAPIView.as_view(),
        name="news-list-create",
    ),
    path(
        "news/import/",
        NewsImportAPIView.as_view(),
        name="news-import",
    ),
    path(
        "news/<slug:slug>/",
        NewsRetrieveUpdateDestroyAPIView.as_view(),
        name="news-detail",
    ),
]
