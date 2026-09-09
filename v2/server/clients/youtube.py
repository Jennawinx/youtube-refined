from __future__ import annotations

import json
import logging
import ssl

from dataclasses import dataclass
from datetime import datetime, timezone

from urllib.parse import urlencode
from urllib.request import urlopen

import certifi
from config import YOUTUBE_API_KEY

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
class YouTubeChannelPlaylist:
    channel_id: str
    name: str
    description: str
    videos: list[YouTubeVideo]


def _parse_publish_date(published_at: str) -> datetime:
    return datetime.fromisoformat(published_at.replace("Z", "+00:00"))


def _parse_duration(iso_duration: str) -> int:
    import re

    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not match:
        return 0
    hours, minutes, seconds = (int(v or 0) for v in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def _api_get(endpoint: str, params: dict) -> dict:
    url = f"{YOUTUBE_API_BASE}/{endpoint}?{urlencode(params)}"
    ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        with urlopen(url, timeout=30, context=ctx) as response:
            response = json.loads(response.read())
            # logger.debug(f"\nAPI response for {endpoint}: \n\t{response}")
            return response
    except Exception as exc:
        logging.exception("YouTube API request failed: %s", endpoint)
        raise YouTubeApiError(f"YouTube API request failed: {endpoint}") from exc


def get_video_details(video_ids: list[str]) -> list[YouTubeVideo]:
    video_data = _api_get(
        "videos",
        {
            "part": "snippet,contentDetails",
            "id": ",".join(video_ids),
            "key": YOUTUBE_API_KEY,
        },
    )

    videos = []
    for item in video_data.get("items", []):
        video_id = item.get("id", "")
        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}).get("url", "")
            or thumbnails.get("standard", {}).get("url", "")
            or thumbnails.get("default", {}).get("url", "")
        )
        thumbnail_url_low_res = thumbnails.get("default", {}).get("url", "")

        videos.append(
            YouTubeVideo(
                video_id=video_id,
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                url=YOUTUBE_VIDEO_URL.format(video_id=video_id),
                thumbnail_url=thumbnail_url,
                thumbnail_url_low_res=thumbnail_url_low_res,
                publish_date=_parse_publish_date(snippet.get("publishedAt", "")),
                duration_seconds=_parse_duration(content_details.get("duration", "")),
                categoryId=snippet.get("categoryId", ""),
            )
        )

    return videos


def get_playlist_videos(
    playlist_id: str, fetch_size: int = FETCH_SIZE
) -> list[YouTubeVideo]:
    playlist_data = _api_get(
        "playlistItems",
        {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": fetch_size * 2,
            "key": YOUTUBE_API_KEY,
        },
    )

    video_ids = [
        snippet["resourceId"]["videoId"]
        for item in playlist_data.get("items", [])
        if (snippet := item.get("snippet", {}))
        and snippet.get("resourceId", {}).get("videoId")
    ]

    if not video_ids:
        return []

    videos = get_video_details(video_ids)

    return [v for v in videos if v.duration_seconds > 180][:fetch_size]


def get_channel_playlist(channel_id: str) -> YouTubeChannelPlaylist:

    channel_data = _api_get(
        "channels",
        {
            "part": "snippet,contentDetails",
            "id": channel_id,
            "key": YOUTUBE_API_KEY,
        },
    )

    items = channel_data.get("items", [])
    if not items:
        raise YouTubeApiError(f"Channel not found: {channel_id}")

    channel_item = items[0]
    snippet = channel_item["snippet"]
    uploads_playlist_id = channel_item["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = get_playlist_videos(uploads_playlist_id)

    return YouTubeChannelPlaylist(
        channel_id=channel_id,
        name=snippet.get("title", ""),
        description=snippet.get("description", ""),
        videos=videos,
    )


def search_channels(query: str) -> list[YouTubeChannelResult]:
    data = _api_get(
        "search",
        {
            "part": "snippet",
            "type": "channel",
            "q": query,
            "maxResults": 5,
            "key": YOUTUBE_API_KEY,
        },
    )
    results = []
    for item in data.get("items", []):
        channel_id = item.get("id", {}).get("channelId", "")
        if not channel_id:
            continue
        snippet = item.get("snippet", {})
        results.append(
            YouTubeChannelResult(
                channel_id=channel_id,
                name=snippet.get("title", ""),
                description=snippet.get("description", ""),
                thumbnail_url=snippet.get("thumbnails", {})
                .get("default", {})
                .get("url", ""),
            )
        )
    return results
