from django.urls import path
from .views import WeatherQueryView

urlpatterns = [
    path('query/', WeatherQueryView.as_view(), name='weather-query'),
]
