from typing import Optional
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from feed.models import Video
from feed.services.schedule import get_rules_schedule
from feed.utils import parse_day, parse_hour, parse_rating

TEST_CHANNEL_ID = "UCSzHO_V894KyTDw3UgZS7gg"
PAGE_SIZE = 20


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
def parse_search_screen (value: str) -> str:
    """Parse search mode; returns 'recommended' | 'all' | 'custom' (default: 'recommend')."""
    if value is None:
        return "recommend"
    
    mode = value.strip().lower()
    return mode if mode in {"recommended", "all", "custom"} else "recommended"

def home(request):
    search_screen = parse_search_screen(request.GET.get("search_screen", "recommended"))
    test_day = parse_day(request.GET.get("test_day", ""))
    test_hour = parse_hour(request.GET.get("test_hour", ""))

    current_time = timezone.localtime()
    current_hour = current_time.hour
    current_day = current_time.strftime("%A").lower()

    day = test_day if test_day is not None else current_day
    hour = test_hour if test_hour is not None else current_hour

    rule_schedule = get_rules_schedule()
    current_rule = None

    search_query = request.GET.get("q", "").strip()
    energy_min = parse_rating(request.GET.get("energy_min", ""))
    energy_max = parse_rating(request.GET.get("energy_max", ""))
    educational_min = parse_rating(request.GET.get("educational_min", ""))
    educational_max = parse_rating(request.GET.get("educational_max", ""))

    videos, has_more, next_offset = get_video_page(
        offset=0,
        search_query=search_query,
        energy_min=energy_min,
        energy_max=energy_max,
        educational_min=educational_min,
        educational_max=educational_max,
    )
    context = {
        "day": day,
        "hour": hour,
        "search_screen": search_screen,
        "videos": videos,
        "has_more": has_more,
        "next_offset": next_offset,
        "search_query": search_query,
        "energy_min": energy_min,
        "energy_max": energy_max,
        "educational_min": educational_min,
        "educational_max": educational_max,
    }

    return render(request, "feed/home.html", context=context)


def home_more_html(request):
    try:
        offset = max(0, int(request.GET.get("offset", 0)))
    except (ValueError, TypeError):
        offset = 0

    search_query = request.GET.get("q", "").strip()
    energy_min = parse_rating(request.GET.get("energy_min", ""))
    energy_max = parse_rating(request.GET.get("energy_max", ""))
    educational_min = parse_rating(request.GET.get("educational_min", ""))
    educational_max = parse_rating(request.GET.get("educational_max", ""))

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
