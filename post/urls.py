from django.urls import path

from post.views import (
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
    PostsImportAPIView,
    PostsListCreateAPIView,
    PostsRetrieveUpdateDestroyAPIView,
    TagListCreateAPIView,
    TagRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "categories/", CategoryListCreateAPIView.as_view(), name="category-list-create"
    ),
    path(
        "categories/<slug:slug>/",
        CategoryRetrieveUpdateDestroyAPIView.as_view(),
        name="category-detail",
    ),
    path("tags/", TagListCreateAPIView.as_view(), name="tag-list-create"),
    path(
        "tags/<slug:slug>/",
        TagRetrieveUpdateDestroyAPIView.as_view(),
        name="tag-detail",
    ),
    path("posts/", PostsListCreateAPIView.as_view(), name="posts-list-create"),
    path("post-import/", PostsImportAPIView.as_view(), name="posts-import"),
    path(
        "posts/<slug:slug>/",
        PostsRetrieveUpdateDestroyAPIView.as_view(),
        name="posts-detail",
    ),
]
