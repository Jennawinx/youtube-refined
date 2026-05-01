from django.shortcuts import render

from feed.models import Channel, Video
from feed.services.rss import RssRefreshError, refresh_channel
from feed.services.openai import categorize_video

TEST_CHANNEL_ID = "UCSzHO_V894KyTDw3UgZS7gg"


def home(request):
    videos = Video.objects.select_related("channel").order_by("-publish_date")[:20]
    context = {
        "videos": videos,
    }

    if request.method == "POST":
        if "test_categorize" in request.POST:
            try:
                result = categorize_video(
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
        else:
            channel = Channel.objects.filter(channel_id=TEST_CHANNEL_ID).first()
            if channel is None:
                context["refetch_error"] = (
                    f"Channel {TEST_CHANNEL_ID} was not found in the database."
                )
            else:
                try:
                    createdCount = refresh_channel(channel)
                    context["refetch_success"] = (
                        f"Refetched {channel.name}: created={createdCount} "
                    )
                except RssRefreshError as exc:
                    context["refetch_error"] = str(exc)

    return render(request, "feed/home.html", context=context)
