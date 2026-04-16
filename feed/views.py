from django.shortcuts import render

from feed.models import Channel
from feed.services.rss import RssRefreshError, refresh_channel

TEST_CHANNEL_ID = "UCSzHO_V894KyTDw3UgZS7gg"


def home(request):
    context = {}

    if request.method == "POST":
        channel = Channel.objects.filter(channel_id=TEST_CHANNEL_ID).first()
        if channel is None:
            context["refetch_error"] = f"Channel {TEST_CHANNEL_ID} was not found in the database."
        else:
            try:
                stats = refresh_channel(channel)
                context["refetch_success"] = (
                    f"Refetched {stats.channel_name}: fetched={stats.fetched} "
                    f"created={stats.created} existing={stats.existing} skipped={stats.skipped}"
                )
            except RssRefreshError as exc:
                context["refetch_error"] = str(exc)

    return render(request, "feed/home.html", context=context)
