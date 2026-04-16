from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from urllib.request import urlopen
from xml.etree import ElementTree

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from feed.models import Channel, Video

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


class RssRefreshError(Exception):
    pass


def refresh_all_channels(*, strict_duration: bool = False) -> list[RefreshStats]:
    return [refresh_channel(channel, strict_duration=strict_duration) for channel in Channel.objects.all()]


def refresh_channel(channel: Channel, *, strict_duration: bool = False) -> RefreshStats:
    xml_bytes = fetch_channel_feed(channel.channel_id)
    parsed_videos = parse_feed(xml_bytes)
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


def parse_feed(xml_bytes: bytes) -> list[ParsedVideo]:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise RssRefreshError("Unable to parse RSS feed") from exc

    feed_data = parse_xml_to_json(root)
    entries = get_as_list(feed_data.get("entry"))
    return [parse_entry(entry) for entry in entries]


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


def get_required_value(data: dict, key: str) -> str:
    value = get_text_value(data.get(key))
    if not value:
        raise RssRefreshError(f"Missing required field: {key}")
    return value


def get_text_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        text_value = value.get("#text", "")
        if isinstance(text_value, str):
            return text_value.strip()
    return ""


def get_alternate_link(entry: dict) -> str:
    for link in get_as_list(entry.get("link")):
        if isinstance(link, dict) and link.get("@rel") == "alternate":
            return link.get("@href", "")
    raise RssRefreshError("Missing alternate link")


def get_attribute_value(value, attribute_name: str) -> str:
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, dict):
        attribute_value = value.get(f"@{attribute_name}", "")
        if isinstance(attribute_value, str):
            return attribute_value.strip()
    return ""


def get_as_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return value[0] if value and isinstance(value[0], dict) else {}
    return {}


def get_as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def parse_xml_to_json(element: ElementTree.Element) -> dict:
    json_ready = {strip_namespace(element.tag): element_to_data(element)}
    return json.loads(json.dumps(json_ready))[strip_namespace(element.tag)]


def element_to_data(element: ElementTree.Element):
    children = list(element)
    attributes = {f"@{strip_namespace(key)}": value for key, value in element.attrib.items()}

    if not children:
        text = (element.text or "").strip()
        if attributes and text:
            return {**attributes, "#text": text}
        if attributes:
            return attributes
        return text

    data = dict(attributes)
    for child in children:
        key = strip_namespace(child.tag)
        child_value = element_to_data(child)
        if key in data:
            if not isinstance(data[key], list):
                data[key] = [data[key]]
            data[key].append(child_value)
        else:
            data[key] = child_value

    text = (element.text or "").strip()
    if text:
        data["#text"] = text
    return data


def strip_namespace(value: str) -> str:
    if value.startswith("{"):
        return value.split("}", 1)[1]
    if ":" in value:
        return value.split(":", 1)[1]
    return value


def parse_published_datetime(value: str) -> datetime:
    parsed = parse_datetime(value)
    if parsed is None:
        raise RssRefreshError(f"Invalid published datetime: {value}")
    return parsed
