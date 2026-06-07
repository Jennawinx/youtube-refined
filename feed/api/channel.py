from asyncio.log import logger
from datetime import timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from feed.models import Channel
from feed.services.youtube_api import fetch_channel_feed, refresh_channel_with_feed

_last_server_refresh = None
_refresh_paused_until = None

SERVER_REFRESH_COOLDOWN = timedelta(minutes=1)
CHANNEL_STALE_THRESHOLD = timedelta(days=1)
CHANNELS_PER_REFRESH = 2
PAUSE_DURATION_WHEN_NO_STALE = timedelta(hours=2)

@require_POST
def api_refresh_stale_channels(request):
    global _last_server_refresh, _refresh_paused_until

    now = timezone.now()

    if _refresh_paused_until is not None and now < _refresh_paused_until:
        return JsonResponse({"refreshed": [], "skipped": "paused"})

    if _last_server_refresh is not None and (now - _last_server_refresh) < SERVER_REFRESH_COOLDOWN:
        return JsonResponse({"refreshed": [], "skipped": "cooldown"})

    stale_cutoff = now - CHANNEL_STALE_THRESHOLD
    stale_channels = list(
        Channel.objects
        .filter(last_updated__lt=stale_cutoff)
        .order_by("last_updated")[:CHANNELS_PER_REFRESH]
    )

    if not stale_channels:
        _refresh_paused_until = now + PAUSE_DURATION_WHEN_NO_STALE
        return JsonResponse({"refreshed": [], "skipped": "no stale channels"})

    _last_server_refresh = now

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
