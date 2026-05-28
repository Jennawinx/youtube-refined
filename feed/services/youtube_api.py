from __future__ import annotations

import json
import logging
import ssl

from dataclasses import dataclass
from datetime import datetime

from urllib.parse import urlencode
from urllib.request import urlopen

import certifi

from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from feed.models import Channel, Video
from feed.services.categorizer_llm import VideoDetails, categorize_videos

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v={video_id}"
FETCH_SIZE = 5


class YouTubeApiError(Exception):
    pass


@dataclass
class YouTubeVideo:
    video_id: str
    title: str
    description: str
    url: str
    thumbnail_url: str
    publish_date: datetime


@dataclass
class YouTubeFeed:
    channel_id: str
    name: str
    videos: list[YouTubeVideo]


def _api_get(endpoint: str, params: dict) -> dict:
    url = f"{YOUTUBE_API_BASE}/{endpoint}?{urlencode(params)}"
    ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        with urlopen(url, timeout=30, context=ctx) as response:
            return json.loads(response.read())
    except Exception as exc:
        logger.exception("YouTube API request failed: %s", endpoint)
        raise YouTubeApiError(f"YouTube API request failed: {endpoint}") from exc


def _fetch_playlist_videos(playlist_id: str, api_key: str) -> list[YouTubeVideo]:
    playlist_data = _api_get("playlistItems", {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": FETCH_SIZE,
        "key": api_key,
    })

    videos = []
    for item in playlist_data.get("items", []):
        snippet = item.get("snippet", {})
        video_id = snippet.get("resourceId", {}).get("videoId", "")

        if not video_id:
            continue

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = thumbnails.get("default", {}).get("url", "")

        videos.append(YouTubeVideo(
            video_id=video_id,
            title=snippet.get("title", ""),
            description=snippet.get("description", ""),
            url=YOUTUBE_VIDEO_URL.format(video_id=video_id),
            thumbnail_url=thumbnail_url,
            publish_date=parse_datetime(snippet.get("publishedAt", "")),
        ))

    return videos


def refresh_channel_with_feed(channel: Channel, feed: YouTubeFeed) -> int:
    # Filter out shorts
    videos_list = [
        v for v in feed.videos if not ("/shorts/" in v.url.lower())
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


def fetch_channel_feed(channel_id: str) -> YouTubeFeed:
    api_key = settings.YOUTUBE_API_KEY

    channel_data = _api_get("channels", {
        "part": "snippet,contentDetails",
        "id": channel_id,
        "key": api_key,
    })

    items = channel_data.get("items", [])
    if not items:
        raise YouTubeApiError(f"Channel not found: {channel_id}")

    channel_item = items[0]
    channel_name = channel_item["snippet"]["title"]
    uploads_playlist_id = channel_item["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = _fetch_playlist_videos(uploads_playlist_id, api_key)

    return YouTubeFeed(
        channel_id=channel_id,
        name=channel_name,
        videos=videos,
    )
