from django.urls import path

from .views import home, test_refetch_channel

urlpatterns = [
    path('', home, name='home'),
    path('test-refetch/', test_refetch_channel, name='test_refetch_channel'),
]
