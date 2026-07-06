from django.urls import path

from case_studies.views import (
    CaseStudyImportAPIView,
    CaseStudyListCreateAPIView,
    CaseStudyRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "case-studies/",
        CaseStudyListCreateAPIView.as_view(),
        name="case-study-list-create",
    ),
    path(
        "case-studies/import/",
        CaseStudyImportAPIView.as_view(),
        name="case-study-import",
    ),
    path(
        "case-studies/<slug:slug>/",
        CaseStudyRetrieveUpdateDestroyAPIView.as_view(),
        name="case-study-detail",
    ),
]
