from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from digobikas.utils.pagination import CustomPagination
from digobikas.utils.permissions import IsAdminOrReadOnly
from empowerment_program.filters import (
    EmpowermentProgramCohortFilter,
    EmpowermentProgramFilter,
)
from empowerment_program.selectors.empowerment_selector import (
    get_cohorts_list,
    get_programs_list,
    get_volunteers_list,
)
from empowerment_program.serializers import (
    CohortVolunteerSerializer,
    EmpowermentProgramCohortSerializer,
    EmpowermentProgramSerializer,
)
from empowerment_program.services.empowerment_service import (
    import_empowerment_programs,
)


class EmpowermentProgramListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = EmpowermentProgramSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EmpowermentProgramFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        return get_programs_list()


class EmpowermentProgramRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = EmpowermentProgramSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return get_programs_list()


class CohortListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = EmpowermentProgramCohortSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EmpowermentProgramCohortFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        return get_cohorts_list()


class CohortRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmpowermentProgramCohortSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return get_cohorts_list()


class CohortVolunteerListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CohortVolunteerSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    pagination_class = CustomPagination

    # Reusing DjangoFilterBackend without a specific filterset class (or we could build one,
    # but basic model filters and list operations are supported out of the box).
    def get_queryset(self):
        return get_volunteers_list()


class CohortVolunteerRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = CohortVolunteerSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "pk"

    def get_queryset(self):
        return get_volunteers_list()


class EmpowermentProgramImportAPIView(APIView):
    """
    Endpoint to import empowerment programs from pages.json and attachments.json files.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            result = import_empowerment_programs()
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
