from django.db import models
from django.utils.text import slugify

from digobikas.utils.models import TimeStampedModel


# Create your models here.
class TeamMember(TimeStampedModel):
    MEMBER_TYPE_CHOICE = (
        ("board_member", "Board Member"),
        ("staff", "Staff"),
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, null=True, blank=True)
    designation = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    image = models.FileField(upload_to="team/images/", null=True, blank=True)
    member_type = models.CharField(
        max_length=50,
        choices=MEMBER_TYPE_CHOICE,
        default="board_member",
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        while TeamMember.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug
        super().save(*args, **kwargs)
