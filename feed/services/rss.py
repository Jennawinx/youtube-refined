from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.request import urlopen

from django.utils import timezone

from feed.models import Channel, Video
from feed.services.rss_parsing import (
    RssRefreshError,
    get_alternate_link,
    get_as_dict,
    get_attribute_value,
    get_required_value,
    get_text_value,
    parse_feed as parse_feed_entries,
    parse_published_datetime,
)

RSS_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
SHORTS_MARKER = "#shorts"
MIN_DURATION_SECONDS = 120


@dataclass
class ParsedVideo:
    video_id: str
    title: str
    description: str
    url: str
    thumbnail_url: str
    publish_date: datetime
    duration_seconds: int | None


@dataclass
class RefreshStats:
    channel_name: str
    fetched: int = 0
    created: int = 0
    existing: int = 0
    skipped_shorts: int = 0
    skipped_short_duration: int = 0
    skipped_missing_duration: int = 0


def refresh_all_channels(*, strict_duration: bool = False) -> list[RefreshStats]:
    return [refresh_channel(channel, strict_duration=strict_duration) for channel in Channel.objects.all()]


def refresh_channel(channel: Channel, *, strict_duration: bool = False) -> RefreshStats:
    xml_bytes = fetch_channel_feed(channel.channel_id)
    parsed_videos = parse_feed_to_videos(xml_bytes)
    stats = RefreshStats(channel_name=channel.name, fetched=len(parsed_videos))

    for parsed_video in parsed_videos:
        skip_reason = get_skip_reason(parsed_video, strict_duration=strict_duration)
        if skip_reason == "shorts":
            stats.skipped_shorts += 1
            continue
        if skip_reason == "short_duration":
            stats.skipped_short_duration += 1
            continue
        if skip_reason == "missing_duration":
            stats.skipped_missing_duration += 1
            continue

        _, created = Video.objects.get_or_create(
            video_id=parsed_video.video_id,
            defaults={
                "channel": channel,
                "title": parsed_video.title,
                "description": parsed_video.description,
                "url": parsed_video.url,
                "thumbnail_url": parsed_video.thumbnail_url,
                "publish_date": parsed_video.publish_date,
                "duration_seconds": parsed_video.duration_seconds,
            },
        )
        if created:
            stats.created += 1
        else:
            stats.existing += 1

    channel.last_updated = timezone.now()
    channel.save(update_fields=["last_updated", "updated_at"])
    return stats


def fetch_channel_feed(channel_id: str) -> bytes:
    url = RSS_FEED_URL.format(channel_id=channel_id)
    try:
        with urlopen(url, timeout=30) as response:
            return response.read()
    except Exception as exc:  # pragma: no cover - network wrapper
        raise RssRefreshError(f"Unable to fetch RSS feed for channel {channel_id}") from exc


def parse_feed_to_videos(xml_bytes: bytes) -> list[ParsedVideo]:
    return [parse_entry(entry) for entry in parse_feed_entries(xml_bytes)]


def parse_feed(xml_bytes: bytes) -> list[ParsedVideo]:
    return parse_feed_to_videos(xml_bytes)


def parse_entry(entry: dict) -> ParsedVideo:
    video_id = get_required_value(entry, "videoId")
    title = get_required_value(entry, "title")
    url = get_alternate_link(entry)
    publish_date = parse_published_datetime(get_required_value(entry, "published"))
    media_group = get_as_dict(entry.get("group"))
    description = get_text_value(media_group.get("description"))
    thumbnail_url = get_attribute_value(media_group.get("thumbnail"), "url")
    duration_seconds = None
    duration_value = get_attribute_value(media_group.get("duration"), "seconds")
    if duration_value:
        duration_seconds = int(duration_value)

    return ParsedVideo(
        video_id=video_id,
        title=title,
        description=description,
        url=url,
        thumbnail_url=thumbnail_url,
        publish_date=publish_date,
        duration_seconds=duration_seconds,
    )


def get_skip_reason(parsed_video: ParsedVideo, *, strict_duration: bool = False) -> str | None:
    if SHORTS_MARKER in parsed_video.description.lower():
        return "shorts"
    if parsed_video.duration_seconds is not None and parsed_video.duration_seconds < MIN_DURATION_SECONDS:
        return "short_duration"
    if strict_duration and parsed_video.duration_seconds is None:
        return "missing_duration"
    return None
