from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from digobikas.utils.pagination import CustomPagination
from digobikas.utils.permissions import IsAdminOrReadOnly
from post.filters import CategoryFilter, PostsFilter, TagFilter
from post.models import Category, Tag
from post.selectors.post_selector import get_posts_list
from post.serializers import CategorySerializer, PostsSerializer, TagSerializer
from post.services.post_service import deduplicate_posts, import_posts_from_json


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CategoryFilter


class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"


class TagListCreateAPIView(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TagFilter


class TagRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"


class PostsListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PostsSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostsFilter

    def get_queryset(self):
        """
        Use selector to fetch optimized queryset (select_related & prefetch_related).
        """
        return get_posts_list()

    def perform_create(self, serializer):
        """
        Inject the authenticated user as the author of the post.
        """
        serializer.save(author=self.request.user)


class PostsRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostsSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        """
        Use selector to fetch optimized queryset (select_related & prefetch_related).
        """
        return get_posts_list()


class PostsImportAPIView(APIView):
    """
    Endpoint to import  from the local .json file.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        file_path = settings.BASE_DIR / "posts.json"
        if not file_path.exists():
            return Response(
                {"error": f".json not found at {file_path}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            result = import_posts_from_json(file_path=file_path, author=request.user)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PostsDeduplicateAPIView(APIView):
    """
    Endpoint to find and delete duplicate posts sharing the same slug.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            result = deduplicate_posts()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

