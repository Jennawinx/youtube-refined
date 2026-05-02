from django.urls import path

from .views import home, subscriptions, subscriptions_create

urlpatterns = [
    path('', home, name='home'),
    path('subscriptions/', subscriptions, name='subscriptions'),
    path('subscriptions/create/', subscriptions_create, name='subscriptions_create'),
]
