from __future__ import annotations
from urllib.request import urlopen
from django.utils import timezone
from feed.models import Channel, Video
from feed.services.openai import VideoDetails, categorize_videos
from feed.services.rss_parsing import (
    RssFeed,
    RssRefreshError,
    parse_xml_feed,
)


RSS_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
SHORTS_MARKER = "#shorts"


def fetch_channel_feed(channel_id: str) -> bytes:
    url = RSS_FEED_URL.format(channel_id=channel_id)
    try:
        with urlopen(url, timeout=30) as response:
            return response.read()
    except Exception as exc:  # pragma: no cover - network wrapper
        raise RssRefreshError(
            f"Unable to fetch RSS feed for channel {channel_id}"
        ) from exc


def refresh_channel_with_feed(channel: Channel, feed: RssFeed) -> int:
    # Filter out shorts
    videos_list = [
        v for v in feed.videos if not (SHORTS_MARKER in v.description.lower())
    ]
    video_ids = {v.video_id for v in videos_list}
    existing_video_ids = set(
        Video.objects.filter(video_id__in=video_ids).values_list("video_id", flat=True)
    )
    new_videos = [v for v in videos_list if v.video_id not in existing_video_ids]
    categorized_videos = categorize_videos(
        [
            VideoDetails(id=v.video_id, thumbnail_url=v.thumbnail_url, title=v.title)
            for v in new_videos
        ]
    )
    createdCount = 0

    print(f"Found {len(new_videos)} new videos for channel {channel.name}")

    for i in range(len(new_videos)):
        video = new_videos[i]
        categorized_video = categorized_videos[i]
        _, created = Video.objects.get_or_create(
            video_id=video.video_id,
            defaults={
                "channel": channel,
                "title": video.title,
                "description": video.description,
                "url": video.url,
                "thumbnail_url": video.thumbnail_url,
                "publish_date": video.publish_date,
                "presentation": categorized_video.presentation,
                "category_tags": categorized_video.topics,
                "energy": categorized_video.energy,
                "educational": categorized_video.educational,
            },
        )
        if created:
            createdCount += 1

    channel.last_updated = timezone.now()
    channel.save(update_fields=["last_updated"])

    return createdCount


def refresh_channel(channel: Channel) -> int:
    xml_bytes = fetch_channel_feed(channel.channel_id)
    feed = parse_xml_feed(xml_bytes)

    return refresh_channel_with_feed(channel, feed)


def refresh_all_channels() -> None:
    for channel in Channel.objects.all():
        refresh_channel(channel)
