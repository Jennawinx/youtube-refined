import logging

from typing import Optional

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from feed.models import Channel, FeedRule, Video
from feed.services.rss import RssRefreshError, fetch_channel_feed, refresh_channel, refresh_channel_with_feed
from feed.services.openai import categorize_videos, topics
from feed.services.rss_parsing import parse_xml_feed

TEST_CHANNEL_ID = "UCSzHO_V894KyTDw3UgZS7gg"
PAGE_SIZE = 20

logger = logging.getLogger(__name__)


def _parse_rating(value: str) -> Optional[int]:
    """Parse a 1-10 rating GET param; returns None if missing/invalid."""
    try:
        v = int(value)
        return v if 1 <= v <= 10 else None
    except (ValueError, TypeError):
        return None


def get_video_page(
    offset: int,
    search_query: str = "",
    energy_min: Optional[int] = None,
    energy_max: Optional[int] = None,
    educational_min: Optional[int] = None,
    educational_max: Optional[int] = None,
) -> tuple[list[Video], bool, int]:
    video_qs = Video.objects.select_related("channel")
    if search_query:
        video_qs = video_qs.filter(
            Q(title__icontains=search_query)
            | Q(channel__name__icontains=search_query)
        )
    if energy_min is not None:
        video_qs = video_qs.filter(energy__gte=energy_min)
    if energy_max is not None:
        video_qs = video_qs.filter(energy__lte=energy_max)
    if educational_min is not None:
        video_qs = video_qs.filter(educational__gte=educational_min)
    if educational_max is not None:
        video_qs = video_qs.filter(educational__lte=educational_max)

    videos_window = list(
        video_qs.order_by("-publish_date")[offset : offset + PAGE_SIZE + 1]
    )
    has_more = len(videos_window) > PAGE_SIZE
    videos = videos_window[:PAGE_SIZE]
    next_offset = offset + len(videos)
    return videos, has_more, next_offset


def home(request):
    search_query = request.GET.get("q", "").strip()
    energy_min = _parse_rating(request.GET.get("energy_min", ""))
    energy_max = _parse_rating(request.GET.get("energy_max", ""))
    educational_min = _parse_rating(request.GET.get("educational_min", ""))
    educational_max = _parse_rating(request.GET.get("educational_max", ""))
    videos, has_more, next_offset = get_video_page(
        offset=0,
        search_query=search_query,
        energy_min=energy_min,
        energy_max=energy_max,
        educational_min=educational_min,
        educational_max=educational_max,
    )
    context = {
        "videos": videos,
        "has_more": has_more,
        "next_offset": next_offset,
        "search_query": search_query,
        "energy_min": energy_min,
        "energy_max": energy_max,
        "educational_min": educational_min,
        "educational_max": educational_max,
    }

    if request.method == "POST":
        try:
            result = categorize_videos(
                [
                    {
                        "thumbnail_url": "https://i.ytimg.com/vi/cTymndypryw/hq720.jpg",
                        "title": "Quiet Night Reset | 夜の静けさ – Relaxing Music to Unwind & Clear Your Mind",
                    }
                ]
            )
            context["categorize_success"] = f"Categorization result: {result}"
        except Exception as exc:
            logger.exception("Categorize request failed")
            context["categorize_error"] = f"Error: {str(exc)}"

    return render(request, "feed/home.html", context=context)


def home_more_html(request):
    try:
        offset = max(0, int(request.GET.get("offset", 0)))
    except (ValueError, TypeError):
        offset = 0

    search_query = request.GET.get("q", "").strip()
    energy_min = _parse_rating(request.GET.get("energy_min", ""))
    energy_max = _parse_rating(request.GET.get("energy_max", ""))
    educational_min = _parse_rating(request.GET.get("educational_min", ""))
    educational_max = _parse_rating(request.GET.get("educational_max", ""))

    videos, has_more, next_offset = get_video_page(
        offset=offset,
        search_query=search_query,
        energy_min=energy_min,
        energy_max=energy_max,
        educational_min=educational_min,
        educational_max=educational_max,
    )
    return render(
        request,
        "feed/home_more.html",
        context={
            "videos": videos,
            "has_more": has_more,
            "next_offset": next_offset,
            "search_query": search_query,
            "energy_min": energy_min,
            "energy_max": energy_max,
            "educational_min": educational_min,
            "educational_max": educational_max,
        },
    )


def subscriptions(request):
    channels = Channel.objects.order_by("name")
    context = {
        "channels": channels,
    }

    if request.method == "POST":
        selected_channel_id = request.POST.get("channel_id", "").strip()
        channel = Channel.objects.filter(channel_id=selected_channel_id).first()
        if channel is None:
            context["refetch_error"] = (
                f"Channel {selected_channel_id or '(none)'} was not found in the database."
            )
        else:
            try:
                created_count = refresh_channel(channel)
                context["refetch_success"] = (
                    f"Refetched {channel.name}: created={created_count}"
                )
            except RssRefreshError as exc:
                logger.exception("Refresh channel request failed for channel_id=%s", channel.channel_id)
                context["refetch_error"] = str(exc)

    return render(request, "feed/subscriptions.html", context=context)


def subscriptions_create(request):
    context = {
        "channel_id": "",
    }

    if request.method == "POST":
        channel_id = request.POST.get("channel_id", "").strip()
        context["channel_id"] = channel_id

        if not channel_id:
            context["create_error"] = "Channel ID is required."
        elif Channel.objects.filter(channel_id=channel_id).exists():
            context["create_error"] = f"Channel {channel_id} already exists."
        else:
            try:
                xml_bytes = fetch_channel_feed(channel_id)
                feed = parse_xml_feed(xml_bytes)

                channel = Channel.objects.create(
                    channel_id=channel_id,
                    name=feed.name,
                    upload_frequency="biweekly",
                )

                refresh_channel_with_feed(channel, feed)

                return redirect("subscriptions")
            except RssRefreshError as exc:
                logger.exception("Create subscription request failed for channel_id=%s", channel_id)
                context["create_error"] = str(exc)
            except Exception:
                logger.exception("Unexpected create subscription failure for channel_id=%s", channel_id)
                context["create_error"] = "Unexpected error while creating subscription."

    return render(request, "feed/subscriptions_create.html", context=context)


def _rule_form_context_from_data(data: dict) -> dict:
    return {
        "name": data.get("name", "").strip(),
        "start_time": data.get("start_time", "").strip(),
        "end_time": data.get("end_time", "").strip(),
        "category_tags_input": data.get("category_tags", "").strip(),
        "min_energy": data.get("min_energy", "").strip(),
        "max_energy": data.get("max_energy", "").strip(),
        "min_educational": data.get("min_educational", "").strip(),
        "max_educational": data.get("max_educational", "").strip(),
    }


def _rule_form_context_from_rule(rule: FeedRule) -> dict:
    return {
        "name": rule.name,
        "start_time": rule.start_time.strftime("%H:%M"),
        "end_time": rule.end_time.strftime("%H:%M"),
        "category_tags_input": ", ".join(rule.category_tags or []),
        "min_energy": rule.min_energy or "",
        "max_energy": rule.max_energy or "",
        "min_educational": rule.min_educational or "",
        "max_educational": rule.max_educational or "",
    }


def _selected_days_from_data(data: dict) -> list[str]:
    return list(data.getlist("days"))


def _parse_rule_form_payload(data: dict) -> tuple[dict, Optional[str]]:
    name = data.get("name", "").strip()
    start_time = data.get("start_time", "").strip()
    end_time = data.get("end_time", "").strip()
    category_tags_input = data.get("category_tags", "").strip()

    min_energy = _parse_rating(data.get("min_energy", ""))
    max_energy = _parse_rating(data.get("max_energy", ""))
    min_educational = _parse_rating(data.get("min_educational", ""))
    max_educational = _parse_rating(data.get("max_educational", ""))

    selected_days = _selected_days_from_data(data)

    if not name:
        return {}, "Rule name is required."
    if not start_time or not end_time:
        return {}, "Start and end time are required."
    if min_energy is not None and max_energy is not None and min_energy > max_energy:
        return {}, "Energy range is invalid: min cannot be greater than max."
    if (
        min_educational is not None
        and max_educational is not None
        and min_educational > max_educational
    ):
        return {}, "Educational range is invalid: min cannot be greater than max."

    category_tags = [tag.strip() for tag in category_tags_input.split(",") if tag.strip()]

    return {
        "name": name,
        "start_time": start_time,
        "end_time": end_time,
        "category_tags": category_tags,
        "monday": "monday" in selected_days,
        "tuesday": "tuesday" in selected_days,
        "wednesday": "wednesday" in selected_days,
        "thursday": "thursday" in selected_days,
        "friday": "friday" in selected_days,
        "saturday": "saturday" in selected_days,
        "sunday": "sunday" in selected_days,
        "min_energy": min_energy,
        "max_energy": max_energy,
        "min_educational": min_educational,
        "max_educational": max_educational,
    }, None


def feed_rules(request):
    context = {
        "rules": FeedRule.objects.order_by("start_time", "name"),
        "success_message": request.GET.get("success", "").strip(),
    }
    return render(request, "feed/feed_rules.html", context=context)


def feed_rules_create(request):
    context = {
        "available_topics": topics,
        "selected_days": [],
        "submit_label": "Create Rule",
        **_rule_form_context_from_data({}),
    }

    if request.method == "POST":
        context.update(_rule_form_context_from_data(request.POST))
        context["selected_days"] = _selected_days_from_data(request.POST)

        payload, error = _parse_rule_form_payload(request.POST)
        if error:
            context["error_message"] = error
            return render(request, "feed/feed_rules_create.html", context=context)

        try:
            FeedRule.objects.create(**payload)
            return redirect(f"{reverse('feed_rules')}?success=Feed+rule+added.")
        except Exception:
            logger.exception("Create feed rule request failed")
            context["error_message"] = "Unable to create feed rule."

    return render(request, "feed/feed_rules_create.html", context=context)


def feed_rules_modify(request, rule_id: int):
    rule = get_object_or_404(FeedRule, id=rule_id)
    context = {
        "rule": rule,
        "available_topics": topics,
        "selected_days": [
            day
            for day in [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            if getattr(rule, day)
        ],
        "submit_label": "Save Changes",
        **_rule_form_context_from_rule(rule),
    }

    if request.method == "POST":
        action = request.POST.get("action", "update").strip()
        if action == "delete":
            rule.delete()
            return redirect(f"{reverse('feed_rules')}?success=Feed+rule+removed.")

        context.update(_rule_form_context_from_data(request.POST))
        context["selected_days"] = _selected_days_from_data(request.POST)

        payload, error = _parse_rule_form_payload(request.POST)
        if error:
            context["error_message"] = error
            return render(request, "feed/feed_rules_modify.html", context=context)

        for key, value in payload.items():
            setattr(rule, key, value)

        try:
            rule.save()
            return redirect(f"{reverse('feed_rules')}?success=Feed+rule+updated.")
        except Exception:
            logger.exception("Update feed rule request failed for rule_id=%s", rule.id)
            context["error_message"] = "Unable to update feed rule."

    return render(request, "feed/feed_rules_modify.html", context=context)
