from django.urls import path

from .views import (
    feed_rules,
    feed_rules_create,
    feed_rules_modify,
    home,
    home_more_html,
    subscriptions,
    subscriptions_create,
)

urlpatterns = [
    path('', home, name='home'),
    path('fragments/videos/', home_more_html, name='home_more_html'),
    path('feed-rules/', feed_rules, name='feed_rules'),
    path('feed-rules/create/', feed_rules_create, name='feed_rules_create'),
    path('feed-rules/<int:rule_id>/modify/', feed_rules_modify, name='feed_rules_modify'),
    path('subscriptions/', subscriptions, name='subscriptions'),
    path('subscriptions/create/', subscriptions_create, name='subscriptions_create'),
]
