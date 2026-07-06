from django.db import models
from django.utils.text import slugify

from digobikas.utils.models import TimeStampedModel

# Create your models here.


class EmpowermentProgram(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Empowerment Program"
        verbose_name_plural = "Empowerment Programs"
        ordering = ["-created_at"]


class EmpowermentProgramCohort(TimeStampedModel):
    program = models.ForeignKey(
        EmpowermentProgram,
        on_delete=models.CASCADE,
        related_name="cohorts",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)

    image = models.FileField(
        upload_to="empowerment_program/cohorts/",
        blank=True,
        null=True,
    )
    image_alt_description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.program.title} - {self.name}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Cohort"
        verbose_name_plural = "Cohorts"
        ordering = ["created_at"]


class CohortVolunteer(TimeStampedModel):
    cohort = models.ForeignKey(
        EmpowermentProgramCohort,
        on_delete=models.CASCADE,
        related_name="volunteers",
    )
    name = models.CharField(max_length=255)
    image = models.FileField(upload_to="empowerment_program/cohort_volunteers/")
    image_alt_description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.cohort.name} - {self.name}"

    class Meta:
        verbose_name = "Cohort Volunteer"
        verbose_name_plural = "Cohort Volunteers"
        ordering = ["created_at"]
