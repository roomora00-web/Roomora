import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return
            
        self.user = self.scope["user"]
        self.room_group_name = f'user_{self.user.id}_notifications'

        try:
            # Join user-specific group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        except Exception as e:
            logger.error(f"WebSocket connection error for user {self.user.id}: {e}")
            await self.close()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            try:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
            except Exception as e:
                logger.error(f"WebSocket disconnect error for user {self.user.id}: {e}")

    # Receive message from room group
    async def notification_message(self, event):
        message = event['message']
        notification_type = event.get('notification_type', 'SYSTEM')
        title = event.get('title', 'Notification')

        # Send message to WebSocket
        try:
            await self.send(text_data=json.dumps({
                'message': message,
                'title': title,
                'type': notification_type,
            }))
        except Exception as e:
            logger.error(f"WebSocket send error for user {self.user.id}: {e}")
