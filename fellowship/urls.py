from django.urls import path

from fellowship.views import (
    FellowshipImportAPIView,
    FellowshipListCreateAPIView,
    FellowshipMemberListCreateAPIView,
    FellowshipMemberRetrieveUpdateDestroyAPIView,
    FellowshipRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "fellowships/",
        FellowshipListCreateAPIView.as_view(),
        name="fellowship-list-create",
    ),
    path(
        "fellowships/import/",
        FellowshipImportAPIView.as_view(),
        name="fellowship-import",
    ),
    path(
        "fellowships/<slug:slug>/",
        FellowshipRetrieveUpdateDestroyAPIView.as_view(),
        name="fellowship-detail",
    ),
    path(
        "fellowship-members/",
        FellowshipMemberListCreateAPIView.as_view(),
        name="fellowship-member-list-create",
    ),
    path(
        "fellowship-members/<slug:slug>/",
        FellowshipMemberRetrieveUpdateDestroyAPIView.as_view(),
        name="fellowship-member-detail",
    ),
]
