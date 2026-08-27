from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from digobikas.utils.pagination import CustomPagination
from digobikas.utils.permissions import IsAdminOrReadOnly
from opportunity.filters import OpportunityFilter
from opportunity.selectors.opportunity_selector import get_opportunities_list
from opportunity.serializers import OpportunitySerializer


class OpportunityListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = OpportunitySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OpportunityFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        return get_opportunities_list()


class OpportunityRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OpportunitySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "pk"

    def get_queryset(self):
        return get_opportunities_list()
