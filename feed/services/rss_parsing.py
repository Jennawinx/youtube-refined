from __future__ import annotations

from datetime import datetime
import json
from xml.etree import ElementTree

from django.utils.dateparse import parse_datetime


class RssRefreshError(Exception):
    pass


def parse_feed(xml_bytes: bytes) -> list[dict]:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise RssRefreshError("Unable to parse RSS feed") from exc

    feed_data = parse_xml_to_json(root)
    return get_as_list(feed_data.get("entry"))


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
