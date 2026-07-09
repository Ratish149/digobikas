from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from digobikas.utils.pagination import CustomPagination
from digobikas.utils.permissions import IsAdminOrReadOnly
from news.filters import NewsFilter
from news.selectors.news_selector import get_news_list
from news.serializers import NewsSerializer
from news.services.news_service import import_news


class NewsListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NewsFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        return get_news_list()


class NewsRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return get_news_list()


class NewsImportAPIView(APIView):
    """
    Endpoint to import news from pages.json and attachments.json files.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            result = import_news()
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
