from django.urls import path

from video.views import (
    VideoListCreateAPIView,
    VideoRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "videos/",
        VideoListCreateAPIView.as_view(),
        name="video-list-create",
    ),
    path(
        "videos/<int:pk>/",
        VideoRetrieveUpdateDestroyAPIView.as_view(),
        name="video-detail",
    ),
]
