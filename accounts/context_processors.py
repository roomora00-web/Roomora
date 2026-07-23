from .models import Notification

def unread_notifications(request):
    """Context processor to inject unread notifications count and recent notifications across all templates."""
    if request.user.is_authenticated:
        recent_notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            'unread_notifications_count': unread_count,
            'recent_header_notifications': recent_notifs
        }
    return {
        'unread_notifications_count': 0,
        'recent_header_notifications': []
    }
