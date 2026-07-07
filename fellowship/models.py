from django.db import models
from django.utils.text import slugify

from digobikas.utils.models import TimeStampedModel

# Create your models here.


class Fellowship(TimeStampedModel):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        while Fellowship.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug
        super().save(*args, **kwargs)


class FellowshipMember(TimeStampedModel):
    fellowship = models.ForeignKey(
        Fellowship, on_delete=models.CASCADE, related_name="members"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, null=True, blank=True)
    description = models.TextField()
    image = models.FileField(upload_to="fellowship/images/")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        while FellowshipMember.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug
        super().save(*args, **kwargs)
