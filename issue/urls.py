from django.urls import path

from issue.views import (
    IssueImportAPIView,
    IssueListCreateAPIView,
    IssueRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "issues/",
        IssueListCreateAPIView.as_view(),
        name="issue-list-create",
    ),
    path(
        "issues/import/",
        IssueImportAPIView.as_view(),
        name="issue-import",
    ),
    path(
        "issues/<slug:slug>/",
        IssueRetrieveUpdateDestroyAPIView.as_view(),
        name="issue-detail",
    ),
]
