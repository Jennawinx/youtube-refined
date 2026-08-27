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
from feed.services.llm_video_categorizer import VideoDetails, categorize_videos_advanced

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v={video_id}"
FETCH_SIZE = 3


class YouTubeApiError(Exception):
    pass


@dataclass
class YouTubeChannelResult:
    channel_id: str
    name: str
    description: str
    thumbnail_url: str


@dataclass
class YouTubeVideo:
    video_id: str
    title: str
    description: str
    url: str
    thumbnail_url: str
    thumbnail_url_low_res: str
    publish_date: datetime
    duration_seconds: int = 0
    categoryId: str = ""


@dataclass
class YouTubeFeed:
    channel_id: str
    name: str
    description: str
    videos: list[YouTubeVideo]


def _parse_duration(iso_duration: str) -> int:
    import re
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not match:
        return 0
    hours, minutes, seconds = (int(v or 0) for v in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def search_channels(query: str) -> list[YouTubeChannelResult]:
    data = _api_get("search", {
        "part": "snippet",
        "type": "channel",
        "q": query,
        "maxResults": 5,
        "key": settings.YOUTUBE_API_KEY,
    })
    results = []
    for item in data.get("items", []):
        channel_id = item.get("id", {}).get("channelId", "")
        if not channel_id:
            continue
        snippet = item.get("snippet", {})
        results.append(YouTubeChannelResult(
            channel_id=channel_id,
            name=snippet.get("title", ""),
            description=snippet.get("description", ""),
            thumbnail_url=snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
        ))
    return results



def _api_get(endpoint: str, params: dict) -> dict:
    url = f"{YOUTUBE_API_BASE}/{endpoint}?{urlencode(params)}"
    ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        with urlopen(url, timeout=30, context=ctx) as response:
            response = json.loads(response.read())
            # logger.debug(f"\nAPI response for {endpoint}: \n\t{response}")
            return response
    except Exception as exc:
        logger.exception("YouTube API request failed: %s", endpoint)
        raise YouTubeApiError(f"YouTube API request failed: {endpoint}") from exc


def _fetch_video_details(video_ids: list[str]) -> list[YouTubeVideo]:
    video_data = _api_get("videos", {
        "part": "snippet,contentDetails",
        "id": ",".join(video_ids),
        "key": settings.YOUTUBE_API_KEY,
    })

    videos = []
    for item in video_data.get("items", []):
        video_id = item.get("id", "")
        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = thumbnails.get("high", {}).get("url", "") or thumbnails.get("standard", {}).get("url", "") or thumbnails.get("default", {}).get("url", "")
        thumbnail_url_low_res = thumbnails.get("default", {}).get("url", "")

        videos.append(YouTubeVideo(
            video_id=video_id,
            title=snippet.get("title", ""),
            description=snippet.get("description", ""),
            url=YOUTUBE_VIDEO_URL.format(video_id=video_id),
            thumbnail_url=thumbnail_url,
            thumbnail_url_low_res=thumbnail_url_low_res,
            publish_date=parse_datetime(snippet.get("publishedAt", "")),
            duration_seconds=_parse_duration(content_details.get("duration", "")),
            categoryId=snippet.get("categoryId", ""),
        ))

    return videos


def _fetch_playlist_videos(playlist_id: str, fetch_size: int = FETCH_SIZE) -> list[YouTubeVideo]:
    playlist_data = _api_get("playlistItems", {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": fetch_size * 2,
        "key": settings.YOUTUBE_API_KEY,
    })

    video_ids = [
        snippet["resourceId"]["videoId"]
        for item in playlist_data.get("items", [])
        if (snippet := item.get("snippet", {})) and snippet.get("resourceId", {}).get("videoId")
    ]

    if not video_ids:
        return []
    
    videos = _fetch_video_details(video_ids)

    return [v for v in videos if v.duration_seconds > 180][:fetch_size]


def fetch_channel_feed(channel_id: str) -> YouTubeFeed:

    channel_data = _api_get("channels", {
        "part": "snippet,contentDetails",
        "id": channel_id,
        "key": settings.YOUTUBE_API_KEY,
    })

    items = channel_data.get("items", [])
    if not items:
        raise YouTubeApiError(f"Channel not found: {channel_id}")

    channel_item = items[0]
    snippet = channel_item["snippet"]
    uploads_playlist_id = channel_item["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = _fetch_playlist_videos(uploads_playlist_id)

    return YouTubeFeed(
        channel_id=channel_id,
        name=snippet.get("title", ""),
        description=snippet.get("description", ""),
        videos=videos,
    )


def refresh_channel_with_feed(channel: Channel, feed: YouTubeFeed) -> int:
    # Filter out shorts
    video_list = feed.videos
    video_ids = {v.video_id for v in video_list}
    existing_video_ids = set(
        Video.objects.filter(video_id__in=video_ids).values_list("video_id", flat=True)
    )
    new_videos = [v for v in video_list if v.video_id not in existing_video_ids]
    categorized_videos = categorize_videos_advanced(
        [
            VideoDetails(id=v.video_id, thumbnail_url=v.thumbnail_url_low_res, title=v.title)
            for v in new_videos
        ]
    )
    createdCount = 0

    logger.info(f"Found {len(new_videos)} new videos for channel {channel.name}")

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