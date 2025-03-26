from django.contrib.auth.models import User
from .models import Notification

def create_notification(recipient, title, message, link=None, is_admin=False):
    """
    Create a notification for a user or for admin
    
    Args:
        recipient: User object or None for admin notification
        title: Notification title
        message: Notification message
        link: Optional URL to link to
        is_admin: Boolean indicating if this is an admin notification
    
    Returns:
        Notification object
    """
    if is_admin:
        # Create notification for all admin users
        admin_users = User.objects.filter(is_staff=True)
        notifications = []
        
        for admin in admin_users:
            notification = Notification(
                recipient=admin,
                title=title,
                message=message,
                link=link,
                is_admin=True
            )
            notifications.append(notification)
        
        # Bulk create notifications
        if notifications:
            Notification.objects.bulk_create(notifications)
            return notifications
        return None
    
    else:
        # Create notification for a specific user
        if recipient:
            notification = Notification(
                recipient=recipient,
                title=title,
                message=message,
                link=link
            )
            notification.save()
            return notification
        return None

