from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import AllowAny

from contact.filters import ContactFilter
from contact.selectors.contact_selector import get_contact_list
from contact.serializers import ContactSerializer
from digobikas.utils.pagination import CustomPagination
from digobikas.utils.permissions import IsAdminOrReadOnly


class ContactListCreateAPIView(generics.ListCreateAPIView):
    """
    Anyone can POST (submit a contact form).
    Only admins can list all submissions.
    """

    serializer_class = ContactSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ContactFilter
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAdminOrReadOnly()]

    def get_queryset(self):
        return get_contact_list()


class ContactRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContactSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "pk"

    def get_queryset(self):
        return get_contact_list()
