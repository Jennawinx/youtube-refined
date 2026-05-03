from django.http import JsonResponse
from django.shortcuts import redirect, render

from feed.models import Channel, Video
from feed.services.rss import RssRefreshError, fetch_channel_feed, refresh_channel, refresh_channel_with_feed
from feed.services.openai import categorize_videos
from feed.services.rss_parsing import parse_xml_feed

TEST_CHANNEL_ID = "UCSzHO_V894KyTDw3UgZS7gg"

PAGE_SIZE = 20

def home(request):
    videos = Video.objects.select_related("channel").order_by("-publish_date")[:PAGE_SIZE]
    context = {
        "videos": videos,
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
            context["categorize_error"] = f"Error: {str(exc)}"

    return render(request, "feed/home.html", context=context)


def home_more(request):
    try:
        offset = max(0, int(request.GET.get("offset", 0)))
    except (ValueError, TypeError):
        offset = 0

    videos = Video.objects.select_related("channel").order_by("-publish_date")[offset : offset + PAGE_SIZE]
    data = [
        {
            "url": v.url,
            "thumbnail_url": v.thumbnail_url,
            "title": v.title,
            "duration_seconds": v.duration_seconds,
            "channel_name": v.channel.name,
            "publish_date": v.publish_date.strftime("%b %-d, %Y"),
            "category_tags": v.category_tags,
            "energy": v.energy,
            "educational": v.educational,
        }
        for v in videos
    ]
    return JsonResponse({"videos": data, "has_more": len(data) == PAGE_SIZE})


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

            xml_bytes = fetch_channel_feed(channel_id)
            feed = parse_xml_feed(xml_bytes)

            channel = Channel.objects.create(
                channel_id=channel_id,
                name=feed.name,
                upload_frequency="biweekly",
            )

            refresh_channel_with_feed(channel, feed)

            return redirect("subscriptions")

    return render(request, "feed/subscriptions_create.html", context=context)
