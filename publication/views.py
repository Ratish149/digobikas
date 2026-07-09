from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from digobikas.utils.pagination import CustomPagination
from digobikas.utils.permissions import IsAdminOrReadOnly
from publication.filters import PublicationFilter
from publication.selectors.publication_selector import get_publications_list
from publication.serializers import PublicationSerializer
from publication.services.publication_service import import_publications


class PublicationListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PublicationSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PublicationFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        return get_publications_list()


class PublicationRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PublicationSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return get_publications_list()


class PublicationImportAPIView(APIView):
    """
    Endpoint to import publications from pages.json and attachments.json files.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            result = import_publications()
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
