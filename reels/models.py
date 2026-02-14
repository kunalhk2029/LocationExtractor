from django.db import models


class ReelJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        ERROR = "error", "Error"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    source_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to="reels/videos/%Y/%m/%d/")

    result_city = models.CharField(max_length=128, blank=True)
    result_country = models.CharField(max_length=128, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    reasoning = models.TextField(blank=True)
    audio_transcript = models.TextField(blank=True)
    raw_response = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    frames_meta = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        return f"ReelJob #{self.pk} ({self.status})"
