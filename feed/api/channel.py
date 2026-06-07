from asyncio.log import logger
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from feed.models import Channel
from feed.services.youtube_api import fetch_channel_feed, refresh_channel_with_feed

'''
    Update the 2 oldest channels
'''
@require_POST
def api_refresh_stale_channels(request):
    stale_channels = list(
        Channel.objects.order_by("last_updated")[:2]
    )

    if not stale_channels:
        return JsonResponse({"refreshed": []})

    results = []
    for channel in stale_channels:
        logger.info("Refreshing channel %s (%s)", channel.name, channel.channel_id)
        try:
            feed = fetch_channel_feed(channel.channel_id)
            created_count = refresh_channel_with_feed(channel, feed)
            results.append({
                "channel_id": channel.channel_id,
                "name": channel.name,
                "created": created_count,
                "error": None,
            })
        except Exception as exc:
            logger.exception("Failed to refresh channel %s: %s", channel.channel_id, exc)
            results.append({
                "channel_id": channel.channel_id,
                "name": channel.name,
                "created": 0,
                "error": str(exc),
            })

    return JsonResponse({"refreshed": results})
