from django.contrib import admin

from .models import Channel, FeedRule, Video


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "channel_id", "upload_frequency", "last_updated", "created_at")
    list_filter = ("upload_frequency", "created_at")
    search_fields = ("name", "channel_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "channel", "publish_date", "duration_seconds", "is_watched", "created_at")
    list_filter = ("channel", "is_watched", "publish_date")
    search_fields = ("title", "video_id")
    readonly_fields = ("video_id", "created_at", "updated_at")


@admin.register(FeedRule)
class FeedRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category_tag",
        "start_time",
        "end_time",
        "min_energy",
        "max_energy",
        "min_educational",
        "max_educational",
    )
    search_fields = ("name", "category_tag")
    readonly_fields = ("created_at", "updated_at")
