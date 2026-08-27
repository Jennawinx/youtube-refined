from asyncio.log import logger
from django.utils import timezone
from typing import Optional
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from feed.models import FeedRule
from feed.services.llm_video_categorizer import COMMON_TOPICS
from feed.services.schedule import cache_rules_schedule, get_rules_schedule
from feed.utils import parse_rating


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

    min_energy = parse_rating(data.get("min_energy", ""))
    max_energy = parse_rating(data.get("max_energy", ""))
    min_educational = parse_rating(data.get("min_educational", ""))
    max_educational = parse_rating(data.get("max_educational", ""))

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
    rules = FeedRule.objects.order_by("start_time", "name")
    schedule = get_rules_schedule()
    current_hour = timezone.localtime(timezone.now()).hour
    
    context = {
        "rules": rules,
        "success_message": request.GET.get("success", "").strip(),
        "schedule": schedule,
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "hours": list(range(24)),
        "current_hour": current_hour,
    }
    return render(request, "feed/feed_rules.html", context=context)


def feed_rules_create(request):
    context = {
        "available_topics": COMMON_TOPICS,
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
            cache_rules_schedule()
            return redirect(f"{reverse('feed_rules')}?success=Feed+rule+added.")
        except Exception:
            logger.exception("Create feed rule request failed")
            context["error_message"] = "Unable to create feed rule."

    return render(request, "feed/feed_rules_create.html", context=context)


def feed_rules_modify(request, rule_id: int):
    rule = get_object_or_404(FeedRule, id=rule_id)
    context = {
        "rule": rule,
        "available_topics": COMMON_TOPICS,
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
        
        # Handle delete
        if action == "delete":
            rule.delete()
            cache_rules_schedule()
            return redirect(f"{reverse('feed_rules')}?success=Feed+rule+removed.")

        context.update(_rule_form_context_from_data(request.POST))
        context["selected_days"] = _selected_days_from_data(request.POST)

        payload, error = _parse_rule_form_payload(request.POST)
        if error:
            context["error_message"] = error
            return render(request, "feed/feed_rules_modify.html", context=context)

        for key, value in payload.items():
            setattr(rule, key, value)

        # Handle update
        try:
            rule.save()
            cache_rules_schedule()
            return redirect(f"{reverse('feed_rules')}?success=Feed+rule+updated.")
        except Exception:
            logger.exception("Update feed rule request failed for rule_id=%s", rule.id)
            context["error_message"] = "Unable to update feed rule."

    return render(request, "feed/feed_rules_modify.html", context=context)
