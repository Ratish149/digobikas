from django.db import transaction

from account.models import CustomUser


def register_user(
    *,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    phone_number: str = "",
    address: str = "",
) -> CustomUser:
    """
    Registers a new CustomUser with username set to email, hashes the password, and cleans values.
    """
    with transaction.atomic():
        email = email.strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValueError("A user with this email already exists.")

        user = CustomUser(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            address=address,
        )
        user.set_password(password)
        user.full_clean()
        user.save()
        return user
