from django.urls import path

from .views import feed_rules, home, home_more_html, subscriptions, subscriptions_create

urlpatterns = [
    path('', home, name='home'),
    path('fragments/videos/', home_more_html, name='home_more_html'),
    path('feed-rules/', feed_rules, name='feed_rules'),
    path('subscriptions/', subscriptions, name='subscriptions'),
    path('subscriptions/create/', subscriptions_create, name='subscriptions_create'),
]
