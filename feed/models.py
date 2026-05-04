from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Channel(models.Model):
    """YouTube channel subscription."""

    channel_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    upload_frequency = models.CharField(max_length=50, default="biweekly")
    last_updated = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Video(models.Model):
    """YouTube video from a subscribed channel."""

    video_id = models.CharField(max_length=255, unique=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="videos")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    url = models.URLField()
    thumbnail_url = models.URLField(blank=True)
    publish_date = models.DateTimeField()
    category_tags = models.JSONField(blank=True, default=list)  # JSON array e.g. ["motivation", "morning-routine"]
    energy = models.IntegerField(default=0)  # 1-10 stimulation rating
    educational = models.IntegerField(default=0)  # 1-10 educational rating
    presentation = models.CharField(max_length=255, default="Vlog")
    duration_seconds = models.IntegerField(null=True, blank=True)
    is_watched = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publish_date"]

    def __str__(self):
        return self.title


class FeedRule(models.Model):
    """Time-based feed rule for lifestyle-aware recommendations."""

    name = models.CharField(max_length=255)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    start_time = models.TimeField()
    end_time = models.TimeField()
    category_tag = models.CharField(max_length=255, null=True, blank=False)
    min_energy = models.PositiveSmallIntegerField(
        null=True,
        blank=False,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    max_energy = models.PositiveSmallIntegerField(
        null=True,
        blank=False,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    min_educational = models.PositiveSmallIntegerField(
        null=True,
        blank=False,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    max_educational = models.PositiveSmallIntegerField(
        null=True,
        blank=False,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return self.name
