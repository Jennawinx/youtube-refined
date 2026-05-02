from django.urls import path

from .views import home, subscriptions

urlpatterns = [
    path('', home, name='home'),
    path('subscriptions/', subscriptions, name='subscriptions'),
]
