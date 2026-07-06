from django.db import models
from django.utils.text import slugify

from digobikas.utils.models import TimeStampedModel


# Create your models here.
class Blog(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    thumbnail_image = models.FileField(
        upload_to="blogs/thumbnails/", blank=True, null=True
    )
    thumbnail_alt_description = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to="blogs/files/", blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)
