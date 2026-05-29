from django.urls import path
from feed.views.rules import (
    feed_rules, 
    feed_rules_create, 
    feed_rules_modify
)
from feed.views.subscriptions import (
    subscriptions,
    subscriptions_create,
    subscriptions_channel_search,
)
from feed.views.feed import (
    home,
)


urlpatterns = [
    path("", home, name="home"),
    path("feed-rules/", feed_rules, name="feed_rules"),
    path("feed-rules/create/", feed_rules_create, name="feed_rules_create"),
    path("feed-rules/<int:rule_id>/modify/", feed_rules_modify, name="feed_rules_modify"),
    path("subscriptions/", subscriptions, name="subscriptions"),
    path("subscriptions/create/", subscriptions_create, name="subscriptions_create"),
    path("subscriptions/channel-search/", subscriptions_channel_search, name="subscriptions_channel_search"),
]
