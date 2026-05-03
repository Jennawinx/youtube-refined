from django.urls import path

from .views import home, home_more_html, subscriptions, subscriptions_create

urlpatterns = [
    path('', home, name='home'),
    path('fragments/videos/', home_more_html, name='home_more_html'),
    path('subscriptions/', subscriptions, name='subscriptions'),
    path('subscriptions/create/', subscriptions_create, name='subscriptions_create'),
]
