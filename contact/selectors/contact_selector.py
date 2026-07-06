from django.db.models import QuerySet

from contact.models import Contact


def get_contact_list() -> QuerySet[Contact]:
    """
    Return all contact submissions.
    """
    return Contact.objects.all()
