from asyncio.log import logger
from django.shortcuts import get_object_or_404, redirect, render
from feed.models import Channel
from feed.services.youtube_api import fetch_channel_feed, refresh_channel_with_feed, search_channels
from feed.services.llm_channel_topic_picker import determine_channel_topics
from feed.services.llm_video_categorizer import COMMON_TOPICS

def subscriptions(request):
    channels = Channel.objects.order_by("name")
    context = {
        "channels": channels,
    }

    if request.method == "POST":
        selected_channel_id = request.POST.get("channel_id", "").strip()
        channel = Channel.objects.filter(channel_id=selected_channel_id).first()
        if channel is None:
            context["error_message"] = (
                f"Channel {selected_channel_id or '(none)'} was not found in the database."
            )
        else:
            try:
                feed = fetch_channel_feed(selected_channel_id)
                created_count = refresh_channel_with_feed(channel, feed)

                context["success_message"] = (
                    f"Refetched {channel.name}: created={created_count}"
                )
            except Exception as exc:
                logger.exception("Refresh channel request failed for channel_id=%s. %s", channel.channel_id, exc)
                context["error_message"] = f"Unexpected error while refreshing channel. {exc}"

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
                tags = determine_channel_topics(feed.description)
                
                channel = Channel.objects.create(
                    channel_id=channel_id,
                    name=feed.name,
                    category_tags=tags,
                    upload_frequency="biweekly",
                )

                refresh_channel_with_feed(channel, feed)

                return redirect("subscriptions")
            except Exception as exc:
                logger.exception("Unexpected create subscription failure for channel_id=%s. %s", channel_id, exc)
                context["create_error"] = f"Unexpected error while creating subscription. {exc}"

    return render(request, "feed/subscriptions_create.html", context=context)


def subscriptions_channel_edit(request, channel_id):
    channel = get_object_or_404(Channel, channel_id=channel_id)
    context = {
        "channel": channel,
        "available_topics": COMMON_TOPICS,
        "category_tags_input": ", ".join(channel.category_tags or []),
        "error_message": None,
    }

    if request.method == "POST":
        action = request.POST.get("action", "update")

        if action == "delete":
            channel.delete()
            return redirect("subscriptions")

        category_tags_input = request.POST.get("category_tags", "").strip()
        context["category_tags_input"] = category_tags_input
        category_tags = [tag.strip() for tag in category_tags_input.split(",") if tag.strip()]
        channel.category_tags = category_tags
        try:
            channel.save(update_fields=["category_tags"])
            return redirect("subscriptions")
        except Exception as exc:
            logger.exception("Update channel tags failed for channel_id=%s. %s", channel_id, exc)
            context["error_message"] = f"Unexpected error while saving. {exc}"

    return render(request, "feed/subscriptions_channel_edit.html", context=context)


def subscriptions_delete(request, channel_id):
    if request.method == "POST":
        Channel.objects.filter(channel_id=channel_id).delete()
    return redirect("subscriptions")


def subscriptions_channel_search(request):
    query = request.GET.get("q", "").strip()
    results = search_channels(query) if query else []
    return render(request, "feed/subscriptions_channel_search_results.html", {"results": results})