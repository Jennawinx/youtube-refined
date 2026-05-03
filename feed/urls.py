from django.urls import path

from .views import home, home_more, subscriptions, subscriptions_create

urlpatterns = [
    path('', home, name='home'),
    path('api/videos/', home_more, name='home_more'),
    path('subscriptions/', subscriptions, name='subscriptions'),
    path('subscriptions/create/', subscriptions_create, name='subscriptions_create'),
]
