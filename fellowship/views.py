from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from digobikas.utils.permissions import IsAdminOrReadOnly
from fellowship.filters import FellowshipFilter, FellowshipMemberFilter
from fellowship.selectors.fellowship_selector import (
    get_fellowship_members_list,
    get_fellowships_list,
)
from fellowship.serializers import FellowshipMemberSerializer, FellowshipSerializer
from fellowship.services.fellowship_service import import_fellowships


class FellowshipListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = FellowshipSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = FellowshipFilter

    def get_queryset(self):
        return get_fellowships_list()


class FellowshipRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FellowshipSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return get_fellowships_list()


class FellowshipMemberListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = FellowshipMemberSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = FellowshipMemberFilter

    def get_queryset(self):
        return get_fellowship_members_list()


class FellowshipMemberRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = FellowshipMemberSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return get_fellowship_members_list()


class FellowshipImportAPIView(APIView):
    """
    Endpoint to import fellowships and members from pages.json and attachments.json files.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            result = import_fellowships()
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
