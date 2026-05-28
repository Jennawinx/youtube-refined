from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v={video_id}"


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
    try:
        with urlopen(url, timeout=30) as response:
            return json.loads(response.read())
    except Exception as exc:
        logger.exception("YouTube API request failed: %s", endpoint)
        raise YouTubeApiError(f"YouTube API request failed: {endpoint}") from exc


def _parse_datetime(value: str) -> datetime:
    parsed = parse_datetime(value)
    if parsed is None:
        raise YouTubeApiError(f"Invalid published datetime: {value}")
    return parsed


def _fetch_playlist_videos(playlist_id: str, api_key: str) -> list[YouTubeVideo]:
    playlist_data = _api_get("playlistItems", {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 50,
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
            publish_date=_parse_datetime(snippet.get("publishedAt", "")),
        ))

    return videos


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
