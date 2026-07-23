import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import Notification

class NotificationService:
    """Service class to handle creating and dispatching notifications"""
    
    @staticmethod
    def send_notification(user, title, message, notification_type='SYSTEM', link='', related_object_id=None, send_email=False, email_template=None, email_context=None):
        """
        Creates a DB record and broadcasts it over WebSockets.
        Optionally sends an HTML email if requested.
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
            
        # 3. Send HTML Email if requested
        if send_email and user.email:
            try:
                context = email_context or {}
                context.update({
                    'user': user,
                    'title': title,
                    'message': message,
                    'link': link,
                    'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
                })
                
                template_name = email_template or 'accounts/emails/booking_update.html'
                html_content = render_to_string(template_name, context)
                
                email = EmailMultiAlternatives(
                    subject=title,
                    body=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'roomora00@gmail.com'),
                    to=[user.email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=True)
            except Exception as e:
                print(f"Failed to send email notification to {user.email}: {str(e)}")
        
        return notification
