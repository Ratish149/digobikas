from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from digobikas.utils.pagination import CustomPagination
from digobikas.utils.permissions import IsAdminOrReadOnly
from team.filters import TeamMemberFilter
from team.selectors.team_selector import get_team_members_list
from team.serializers import TeamMemberSerializer
from team.services.team_service import import_team


class TeamMemberListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TeamMemberFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        return get_team_members_list()


class TeamMemberRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return get_team_members_list()


class TeamImportAPIView(APIView):
    """
    Endpoint to import team members (board members & staff) from pages.json/attachments.json.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            result = import_team()
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
