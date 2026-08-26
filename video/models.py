from django.db import models


class Video(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return self.title
