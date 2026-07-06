from django.db import models

from digobikas.utils.models import TimeStampedModel


# Create your models here.
class Contact(TimeStampedModel):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=255)
    message = models.TextField()

    def __str__(self):
        return self.name
