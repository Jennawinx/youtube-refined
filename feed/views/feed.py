from enum import StrEnum
from typing import Optional
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from feed.models import Video
from feed.services.schedule import get_current_time_block
from feed.utils import parse_week_day, parse_hour, parse_rating

TEST_CHANNEL_ID = "UCSzHO_V894KyTDw3UgZS7gg"
PAGE_SIZE = 20


class ScreenType(StrEnum):
    RECOMMENDED = "recommended"
    ALL = "all"
    CUSTOM = "custom"


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


# TODO: custom maybe some saved filter from the db
def parse_screen_type (value: Optional[str]) -> str:
    """Parse screen type from GET param; defaults to RECOMMENDED if missing/invalid."""
    if value is None:
        return ScreenType.RECOMMENDED
    
    mode = value.strip().lower()
    return mode if mode in {ScreenType.RECOMMENDED, ScreenType.ALL, ScreenType.CUSTOM} else ScreenType.RECOMMENDED


def home(request):
    try:
        offset = max(0, int(request.GET.get("offset", 0)))
    except (ValueError, TypeError):
        offset = 0

    screen_type = parse_screen_type(request.GET.get("screen_type"))
    test_day = parse_week_day(request.GET.get("test_day"))
    test_hour = parse_hour(request.GET.get("test_hour"))

    current_time = timezone.localtime()
    current_hour = current_time.hour
    current_day = current_time.strftime("%A").lower()

    day = test_day if test_day is not None else parse_week_day(current_day)
    hour = test_hour if test_hour is not None else current_hour

    current_rule = get_current_time_block(day, hour)

    print(f"Parsed test_day: {test_day}, test_hour: {test_hour}")
    print(f"Current time: {current_time}, day: {day}, hour: {hour}, active rule: {current_rule.rule_name if current_rule else None}")
    print(f"Current screen: {screen_type}")

    search_query = request.GET.get("q", "").strip()
    search_energy_min = parse_rating(request.GET.get("energy_min"))
    search_energy_max = parse_rating(request.GET.get("energy_max"))
    search_educational_min = parse_rating(request.GET.get("educational_min"))
    search_educational_max = parse_rating(request.GET.get("educational_max"))

    context = {
        "day": day,
        "hour": hour,
        "screen_type": screen_type,
        "current_rule": current_rule,
        "offset": offset,
        "search_query": search_query,
        "energy_min": search_energy_min,
        "energy_max": search_energy_max,
        "educational_min": search_educational_min,
        "educational_max": search_educational_max,
    }

    videos, has_more, next_offset = get_video_page(
        offset=context["offset"],
        search_query=context["search_query"],
        energy_min=context["energy_min"],
        energy_max=context["energy_max"],
        educational_min=context["educational_min"],
        educational_max=context["educational_max"],
    )

    context.update({
        "videos": videos,
        "has_more": has_more,
        "next_offset": next_offset,
    })
    
    if offset == 0:
        return render(request, "feed/home.html", context=context)
    else: 
        return render(request, "feed/home_more.html", context=context)
