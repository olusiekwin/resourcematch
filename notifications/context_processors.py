from .models import Notification

def notifications(request):
    """
    Context processor to add notifications to all templates
    """
    context_data = {
        'notifications': [],
        'unread_notifications_count': 0
    }
    
    if request.user.is_authenticated:
        # Get 5 most recent notifications
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:5]
        
        # Count unread notifications
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        context_data['notifications'] = notifications
        context_data['unread_notifications_count'] = unread_count
    
    return context_data

