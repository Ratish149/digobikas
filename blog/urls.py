from django.urls import path

from blog.views import (
    BlogImportAPIView,
    BlogListCreateAPIView,
    BlogRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "blogs/",
        BlogListCreateAPIView.as_view(),
        name="blog-list-create",
    ),
    path(
        "blogs/import/",
        BlogImportAPIView.as_view(),
        name="blog-import",
    ),
    path(
        "blogs/<slug:slug>/",
        BlogRetrieveUpdateDestroyAPIView.as_view(),
        name="blog-detail",
    ),
]
