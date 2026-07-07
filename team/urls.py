from django.urls import path

from team.views import (
    TeamImportAPIView,
    TeamMemberListCreateAPIView,
    TeamMemberRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "team-members/",
        TeamMemberListCreateAPIView.as_view(),
        name="team-member-list-create",
    ),
    path(
        "team-members/import/",
        TeamImportAPIView.as_view(),
        name="team-member-import",
    ),
    path(
        "team-members/<slug:slug>/",
        TeamMemberRetrieveUpdateDestroyAPIView.as_view(),
        name="team-member-detail",
    ),
]
