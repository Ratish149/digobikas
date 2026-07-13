from django.urls import path

from empowerment_program.views import (
    CohortListCreateAPIView,
    CohortRetrieveUpdateDestroyAPIView,
    CohortVolunteerListCreateAPIView,
    CohortVolunteerRetrieveUpdateDestroyAPIView,
    EmpowermentProgramImportAPIView,
    EmpowermentProgramListCreateAPIView,
    EmpowermentProgramRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "empowerment-programs/",
        EmpowermentProgramListCreateAPIView.as_view(),
        name="empowerment-program-list-create",
    ),
    path(
        "empowerment-programs/import/",
        EmpowermentProgramImportAPIView.as_view(),
        name="empowerment-program-import",
    ),
    path(
        "empowerment-programs/<slug:slug>/",
        EmpowermentProgramRetrieveUpdateDestroyAPIView.as_view(),
        name="empowerment-program-detail",
    ),
    path(
        "cohorts/",
        CohortListCreateAPIView.as_view(),
        name="cohort-list-create",
    ),
    path(
        "cohorts/<slug:slug>/",
        CohortRetrieveUpdateDestroyAPIView.as_view(),
        name="cohort-detail",
    ),
    path(
        "cohort-volunteers/",
        CohortVolunteerListCreateAPIView.as_view(),
        name="cohort-volunteer-list-create",
    ),
    path(
        "cohort-volunteers/<int:pk>/",
        CohortVolunteerRetrieveUpdateDestroyAPIView.as_view(),
        name="cohort-volunteer-detail",
    ),
]
