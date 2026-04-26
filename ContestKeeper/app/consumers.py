import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LeaderboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.contest_id = self.scope['url_route']['kwargs']['contest_id']
        self.room_group_name = f'leaderboard_{self.contest_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def leaderboard_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': 'update'
        }))
