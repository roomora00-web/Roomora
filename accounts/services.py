import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification

class NotificationService:
    """Service class to handle creating and dispatching notifications"""
    
    @staticmethod
    def send_notification(user, title, message, notification_type='SYSTEM', link='', related_object_id=None):
        """
        Creates a DB record and broadcasts it over WebSockets.
        In a full Celery setup, this would also queue an email/SMS task if needed.
        """
        # 1. Save to database
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
            related_object_id=related_object_id
        )
        
        # 2. Broadcast via Channels
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f'user_{user.id}_notifications'
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'notification_message',
                    'message': message,
                    'title': title,
                    'notification_type': notification_type,
                    'link': link,
                    'id': notification.id,
                }
            )
            
        # 3. (Optional) Dispatch Celery task for Email/SMS here
        # e.g., send_notification_email.delay(user.id, title, message)
        
        return notification
