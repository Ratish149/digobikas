from django.db import transaction

from contact.models import Contact


def create_contact(
    *,
    name: str,
    email: str,
    phone: str,
    message: str,
) -> Contact:
    with transaction.atomic():
        contact = Contact(
            name=name,
            email=email,
            phone=phone,
            message=message,
        )
        contact.full_clean()
        contact.save()
        return contact


def update_contact(*, contact: Contact, **data) -> Contact:
    with transaction.atomic():
        for field, value in data.items():
            setattr(contact, field, value)
        contact.full_clean()
        contact.save()
        return contact
