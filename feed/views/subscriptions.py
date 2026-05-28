from asyncio.log import logger
from django.shortcuts import redirect, render
from feed.models import Channel
from feed.services.youtube_api import fetch_channel_feed, refresh_channel_with_feed

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
                feed = fetch_channel_feed(selected_channel_id)
                created_count = refresh_channel_with_feed(channel, feed)

                context["refetch_success"] = (
                    f"Refetched {channel.name}: created={created_count}"
                )
            except Exception as exc:
                logger.exception("Refresh channel request failed for channel_id=%s. %s", channel.channel_id, exc)
                context["refetch_error"] = f"Unexpected error while refreshing channel. {exc}"

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
                feed = fetch_channel_feed(channel_id)
                channel = Channel.objects.create(
                    channel_id=channel_id,
                    name=feed.name,
                    upload_frequency="biweekly",
                )

                refresh_channel_with_feed(channel, feed)

                return redirect("subscriptions")
            except Exception as exc:
                logger.exception("Unexpected create subscription failure for channel_id=%s. %s", channel_id, exc)
                context["create_error"] = f"Unexpected error while creating subscription. {exc}"

    return render(request, "feed/subscriptions_create.html", context=context)