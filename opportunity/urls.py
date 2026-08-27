from django.urls import path

from opportunity.views import (
    OpportunityListCreateAPIView,
    OpportunityRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "opportunities/",
        OpportunityListCreateAPIView.as_view(),
        name="opportunity-list-create",
    ),
    path(
        "opportunities/<int:pk>/",
        OpportunityRetrieveUpdateDestroyAPIView.as_view(),
        name="opportunity-detail",
    ),
]
