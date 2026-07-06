from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from case_studies.filters import CaseStudyFilter
from case_studies.selectors.case_study_selector import get_case_studies_list
from case_studies.serializers import CaseStudySerializer
from case_studies.services.case_study_service import import_case_studies
from digobikas.utils.permissions import IsAdminOrReadOnly


class CaseStudyListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CaseStudySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CaseStudyFilter

    def get_queryset(self):
        return get_case_studies_list()


class CaseStudyRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CaseStudySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return get_case_studies_list()


class CaseStudyImportAPIView(APIView):
    """
    Endpoint to import case studies from pages.json and attachments.json files.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            result = import_case_studies()
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
