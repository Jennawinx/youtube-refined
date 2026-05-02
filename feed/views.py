from django.shortcuts import render

from feed.models import Channel, Video
from feed.services.rss import RssRefreshError, refresh_channel
from feed.services.openai import categorize_videos

TEST_CHANNEL_ID = "UCSzHO_V894KyTDw3UgZS7gg"

def home(request):
    videos = Video.objects.select_related("channel").order_by("-publish_date")[:20]
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
