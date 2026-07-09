from django.conf import settings
from django.db import models
from django.utils.text import slugify

from digobikas.utils.models import TimeStampedModel

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(TimeStampedModel):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, null=True, blank=True)
    content = models.TextField()
    thumbnail = models.FileField(upload_to="post_thumbnails/", blank=True, null=True)
    thumbnail_alt_description = models.CharField(max_length=255, blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="posts",
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField("Tag", related_name="posts")
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)
