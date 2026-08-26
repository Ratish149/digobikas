from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from digobikas.utils.pagination import CustomPagination
from digobikas.utils.permissions import IsAdminOrReadOnly
from video.filters import VideoFilter
from video.selectors.video_selector import get_videos_list
from video.serializers import VideoSerializer


class VideoListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = VideoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = VideoFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        return get_videos_list()


class VideoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VideoSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "pk"

    def get_queryset(self):
        return get_videos_list()
