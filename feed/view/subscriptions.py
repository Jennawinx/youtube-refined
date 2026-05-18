from asyncio.log import logger
from django.shortcuts import redirect, render
from feed.models import Channel
from feed.services.rss import RssRefreshError, fetch_channel_feed, refresh_channel, refresh_channel_with_feed
from feed.services.rss_parsing import parse_xml_feed

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
                logger.exception("Refresh channel request failed for channel_id=%s", channel.channel_id)
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
            try:
                xml_bytes = fetch_channel_feed(channel_id)
                feed = parse_xml_feed(xml_bytes)

                channel = Channel.objects.create(
                    channel_id=channel_id,
                    name=feed.name,
                    upload_frequency="biweekly",
                )

                refresh_channel_with_feed(channel, feed)

                return redirect("subscriptions")
            except RssRefreshError as exc:
                logger.exception("Create subscription request failed for channel_id=%s", channel_id)
                context["create_error"] = str(exc)
            except Exception:
                logger.exception("Unexpected create subscription failure for channel_id=%s", channel_id)
                context["create_error"] = "Unexpected error while creating subscription."

    return render(request, "feed/subscriptions_create.html", context=context)