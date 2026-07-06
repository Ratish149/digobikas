from django.urls import path

from publication.views import (
    PublicationImportAPIView,
    PublicationListCreateAPIView,
    PublicationRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "publications/",
        PublicationListCreateAPIView.as_view(),
        name="publication-list-create",
    ),
    path(
        "publications/import/",
        PublicationImportAPIView.as_view(),
        name="publication-import",
    ),
    path(
        "publications/<slug:slug>/",
        PublicationRetrieveUpdateDestroyAPIView.as_view(),
        name="publication-detail",
    ),
]
