import re

with open('bookings/services/notification_service.py', 'r') as f:
    content = f.read()

content = content.replace('from accounts.models import Notification', '''from accounts.services import NotificationService as CoreNotificationService

def _send_notification(**kwargs):
    if not kwargs.get('user'):
        return
    CoreNotificationService.send_notification(
        user=kwargs.get('user'),
        title=kwargs.get('title'),
        message=kwargs.get('message'),
        notification_type=kwargs.get('notification_type', 'INFO'),
        send_email=True,
        email_template='accounts/emails/booking_update.html'
    )''')

content = content.replace('Notification.objects.create', '_send_notification')

with open('bookings/services/notification_service.py', 'w') as f:
    f.write(content)
