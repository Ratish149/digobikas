from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from digobikas.utils.pagination import CustomPagination
from digobikas.utils.permissions import IsAdminOrReadOnly
from issue.filters import IssueFilter
from issue.selectors.issue_selector import get_issues_list
from issue.serializers import IssueSerializer
from issue.services.issue_service import import_issues


class IssueListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IssueFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        return get_issues_list()


class IssueRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return get_issues_list()


class IssueImportAPIView(APIView):
    """
    Endpoint to import issues from the local pages.json and attachments.json files.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            result = import_issues()
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
