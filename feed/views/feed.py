from enum import StrEnum
from typing import Optional
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from feed.models import Video
from feed.services.categorizer_llm import topics
from feed.services.schedule import get_current_time_block
from feed.utils import find_max, find_min, parse_week_day, parse_hour, parse_rating, parse_comma_list


TEST_CHANNEL_ID = "UCSzHO_V894KyTDw3UgZS7gg"
PAGE_SIZE       = 20


class ScreenType(StrEnum):
    RECOMMENDED = "feed"
    ALL         = "all"
    CUSTOM      = "custom"


def get_video_page(
    offset:                 int,
    search_query:           str = "",
    energy_min:             Optional[int] = None,
    energy_max:             Optional[int] = None,
    educational_min:        Optional[int] = None,
    educational_max:        Optional[int] = None,
    category_tags:          list[str] = [],
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

    if category_tags:
        category_tag_q = Q()
        for tag in category_tags:
            category_tag_q |= Q(category_tags__icontains=tag)
        video_qs = video_qs.filter(category_tag_q)

    videos_window = list(
        video_qs.order_by("-publish_date")[offset : offset + PAGE_SIZE + 1]
    )

    has_more        = len(videos_window) > PAGE_SIZE
    videos          = videos_window[:PAGE_SIZE]
    next_offset     = offset + len(videos)

    return videos, has_more, next_offset


# TODO: custom maybe some saved filter from the db
def parse_screen_type(value: Optional[str]) -> str:
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

    screen_type     = parse_screen_type(request.GET.get("screen_type"))
    test_day        = parse_week_day(request.GET.get("test_day"))
    test_hour       = parse_hour(request.GET.get("test_hour"))

    current_time    = timezone.localtime()
    current_hour    = current_time.hour
    current_day     = current_time.strftime("%A").lower()

    day             = test_day if test_day is not None else parse_week_day(current_day)
    hour            = test_hour if test_hour is not None else current_hour

    current_rule    = get_current_time_block(day, hour)

    print(f"Current screen: {screen_type}")
    print(f"Current time: {current_time}, day: {day}, hour: {hour}, active rule: {current_rule.rule_name if current_rule else None}")
    print(f"Parsed test_day: {test_day}, test_hour: {test_hour}")
    print()

    search_query                = request.GET.get("q", "").strip()
    search_energy_min           = parse_rating(request.GET.get("energy_min"))
    search_energy_max           = parse_rating(request.GET.get("energy_max"))
    search_educational_min      = parse_rating(request.GET.get("educational_min"))
    search_educational_max      = parse_rating(request.GET.get("educational_max"))
    search_category_tags        = parse_comma_list(request.GET.get("category_tags"))

    context = {
        "day": day,
        "hour": hour,
        "test_day": test_day,
        "test_hour": test_hour,
        "screen_options": [ScreenType.RECOMMENDED, ScreenType.ALL, ScreenType.CUSTOM],
        "screen_type": screen_type,
        "current_rule": current_rule,
        "offset": offset,
        "search_query": search_query,
        "all_category_tags": topics,
    }

    if screen_type == ScreenType.CUSTOM:
        # TODO:
        context["energy_min"]       = search_energy_min
        context["energy_max"]       = search_energy_max
        context["educational_min"]  = search_educational_min
        context["educational_max"]  = search_educational_max
        context["category_tags"]    = search_category_tags
        context["category_tags_str"]= ",".join(search_category_tags)

    elif screen_type == ScreenType.RECOMMENDED and current_rule is not None:
        context["energy_min"]       = find_max([search_energy_min, current_rule.min_energy])
        context["energy_max"]       = find_min([search_energy_max, current_rule.max_energy])
        context["educational_min"]  = find_max([search_educational_min, current_rule.min_educational])
        context["educational_max"]  = find_min([search_educational_max, current_rule.max_educational])
        context["category_tags"]    = list(set(current_rule.category_tags + search_category_tags))
        context["category_tags_str"]= ",".join(context["category_tags"])

    else: # ScreenType.ALL
        context["energy_min"]       = search_energy_min
        context["energy_max"]       = search_energy_max
        context["educational_min"]  = search_educational_min
        context["educational_max"]  = search_educational_max
        context["category_tags"]    = search_category_tags
        context["category_tags_str"]= ",".join(search_category_tags)

    videos, has_more, next_offset = get_video_page(
        offset                  = context["offset"],
        search_query            = context["search_query"],
        energy_min              = context["energy_min"],
        energy_max              = context["energy_max"],
        educational_min         = context["educational_min"],
        educational_max         = context["educational_max"],
        category_tags  = context["category_tags"],
    )

    context.update({
        "videos":       videos,
        "has_more":     has_more,
        "next_offset":  next_offset,
    })

    if offset == 0:
        return render(request, "feed/home.html", context=context)
    else:
        return render(request, "feed/home_more.html", context=context)
