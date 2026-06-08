from django.urls import path
from feed.views.rules import (
    feed_rules,
    feed_rules_create,
    feed_rules_modify
)
from feed.views.subscriptions import (
    subscriptions,
    subscriptions_create,
    subscriptions_channel_edit,
    subscriptions_delete,
    subscriptions_channel_search,
)
from feed.views.feed import (
    home,
)
from feed.api.channel import (
    api_refresh_stale_channels,
)


urlpatterns = [
    path("", home, name="home"),
    path("api/channels/refresh-stale-channels/", api_refresh_stale_channels, name="api_refresh_stale_channels"),
    path("feed-rules/", feed_rules, name="feed_rules"),
    path("feed-rules/create/", feed_rules_create, name="feed_rules_create"),
    path("feed-rules/<int:rule_id>/modify/", feed_rules_modify, name="feed_rules_modify"),
    path("subscriptions/", subscriptions, name="subscriptions"),
    path("subscriptions/create/", subscriptions_create, name="subscriptions_create"),
    path("subscriptions/<str:channel_id>/edit/", subscriptions_channel_edit, name="subscriptions_channel_edit"),
    path("subscriptions/<str:channel_id>/delete/", subscriptions_delete, name="subscriptions_delete"),
    path("subscriptions/channel-search/", subscriptions_channel_search, name="subscriptions_channel_search"),
]
