from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from xml.etree import ElementTree

from django.utils.dateparse import parse_datetime


class RssRefreshError(Exception):
    pass

@dataclass
class ParsedVideo:
    video_id: str
    title: str
    description: str
    url: str
    thumbnail_url: str
    publish_date: datetime

def parse_xml_feed(xml_bytes: bytes) -> list[ParsedVideo]:
    return [_serialize_video(entry) for entry in _json_feed(xml_bytes)]

def _json_feed(xml_bytes: bytes) -> list[dict]:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise RssRefreshError("Unable to parse RSS feed") from exc

    feed_data = _parse_xml_to_json(root)
    return _get_as_list(feed_data.get("entry"))

def _serialize_video(entry: dict) -> ParsedVideo:
    media_group = _get_as_dict(entry.get("group"))

    return ParsedVideo(
        video_id=_get_required_value(entry, "videoId"),
        title=_get_required_value(entry, "title"),
        description=_get_text_value(media_group.get("description")),
        url=_get_alternate_link(entry),
        thumbnail_url=_get_attribute_value(media_group.get("thumbnail"), "url"),
        publish_date=_parse_published_datetime(_get_required_value(entry, "published")),
    )

def _get_required_value(data: dict, key: str) -> str:
    value = _get_text_value(data.get(key))
    if not value:
        raise RssRefreshError(f"Missing required field: {key}")
    return value


def _get_text_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        text_value = value.get("#text", "")
        if isinstance(text_value, str):
            return text_value.strip()
    return ""


def _get_alternate_link(entry: dict) -> str:
    for link in _get_as_list(entry.get("link")):
        if isinstance(link, dict) and link.get("@rel") == "alternate":
            return link.get("@href", "")
    raise RssRefreshError("Missing alternate link")


def _get_attribute_value(value, attribute_name: str) -> str:
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, dict):
        attribute_value = value.get(f"@{attribute_name}", "")
        if isinstance(attribute_value, str):
            return attribute_value.strip()
    return ""


def _get_as_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return value[0] if value and isinstance(value[0], dict) else {}
    return {}


def _get_as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _parse_xml_to_json(element: ElementTree.Element) -> dict:
    json_ready = {_strip_namespace(element.tag): _element_to_data(element)}
    return json.loads(json.dumps(json_ready))[_strip_namespace(element.tag)]


def _element_to_data(element: ElementTree.Element):
    children = list(element)
    attributes = {f"@{_strip_namespace(key)}": value for key, value in element.attrib.items()}

    if not children:
        text = (element.text or "").strip()
        if attributes and text:
            return {**attributes, "#text": text}
        if attributes:
            return attributes
        return text

    data = dict(attributes)
    for child in children:
        key = _strip_namespace(child.tag)
        child_value = _element_to_data(child)
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


def _strip_namespace(value: str) -> str:
    if value.startswith("{"):
        return value.split("}", 1)[1]
    if ":" in value:
        return value.split(":", 1)[1]
    return value


def _parse_published_datetime(value: str) -> datetime:
    parsed = parse_datetime(value)
    if parsed is None:
        raise RssRefreshError(f"Invalid published datetime: {value}")
    return parsed

