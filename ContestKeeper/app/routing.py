from django.urls import re_path
from app import consumers

websocket_urlpatterns = [
    re_path(r'ws/leaderboard/(?P<contest_id>\d+)/$', consumers.LeaderboardConsumer.as_asgi()),
]
