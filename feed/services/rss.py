from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.request import urlopen

from django.utils import timezone

from feed.models import Channel, Video
from feed.services.rss_parsing import (
    RssRefreshError,
    ParsedVideo,
    parse_xml_feed,
)

RSS_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
SHORTS_MARKER = "#shorts"

@dataclass
class RefreshStats:
    channel_name: str
    fetched: int = 0
    created: int = 0
    existing: int = 0
    skipped: int = 0

def fetch_channel_feed(channel_id: str) -> bytes:
    url = RSS_FEED_URL.format(channel_id=channel_id)
    try:
        with urlopen(url, timeout=30) as response:
            return response.read()
    except Exception as exc:  # pragma: no cover - network wrapper
        raise RssRefreshError(f"Unable to fetch RSS feed for channel {channel_id}") from exc

def refresh_channel(channel: Channel) -> RefreshStats:
    xml_bytes = fetch_channel_feed(channel.channel_id)
    parsed_videos = parse_xml_feed(xml_bytes)
    print(f"Fetched {len(parsed_videos)} videos for channel {channel.name}")
    print(parsed_videos)
    stats = RefreshStats(channel_name=channel.name, fetched=len(parsed_videos))

    for parsed_video in parsed_videos:
        if SHORTS_MARKER in parsed_video.description.lower():
            stats.skipped += 1
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
            },
        )
        if created:
            stats.created += 1
        else:
            stats.existing += 1

    channel.last_updated = timezone.now()
    channel.save(update_fields=["last_updated", "updated_at"])
    return stats

def refresh_all_channels() -> list[RefreshStats]:
    return [refresh_channel(channel) for channel in Channel.objects.all()]