from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField


# Create your models here.
class Opportunity(models.Model):
    TYPE_CHOICES = (
        ("Fellowship", "Fellowship"),
        ("Internship", "Internship"),
        ("Grants", "Grants"),
        ("Vacancy", "Vacancy"),
    )
    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, null=True, blank=True)
    description = HTMLField()
    image = models.FileField(upload_to="opportunity/images/", null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    apply_by = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)
