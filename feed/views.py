from django.shortcuts import render
from django.views.decorators.http import require_POST

from feed.models import Channel
from feed.services.rss import RssRefreshError, refresh_channel

TEST_CHANNEL_ID = "UCSzHO_V894KyTDw3UgZS7gg"


def home(request):
    return render(request, "feed/home.html")


@require_POST
def test_refetch_channel(request):
    channel = Channel.objects.filter(channel_id=TEST_CHANNEL_ID).first()
    if channel is None:
        context = {
            "refetch_error": f"Channel {TEST_CHANNEL_ID} was not found in the database.",
        }
        return render(request, "feed/home.html", context=context)

    try:
        stats = refresh_channel(channel)
    except RssRefreshError as exc:
        context = {
            "refetch_error": str(exc),
        }
        return render(request, "feed/home.html", context=context)

    context = {
        "refetch_success": (
            f"Refetched {stats.channel_name}: fetched={stats.fetched} "
            f"created={stats.created} existing={stats.existing} skipped={stats.skipped}"
        )
    }
    return render(request, "feed/home.html", context=context)
