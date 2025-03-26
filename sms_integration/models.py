from django.db import models
from django.conf import settings
from accounts.models import UserProfile

class SMSTemplate(models.Model):
    """Model for storing SMS templates"""
    name = models.CharField(max_length=100)
    template_text = models.TextField(help_text="Use {variable} for dynamic content")
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class SMSLog(models.Model):
    """Model for logging SMS messages sent"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    )
    
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sms_logs')
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    template = models.ForeignKey(SMSTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    external_id = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"SMS to {self.phone_number} - {self.status}"
    
    class Meta:
        verbose_name = "SMS Log"
        verbose_name_plural = "SMS Logs"
        ordering = ['-sent_at']

class SMSPreference(models.Model):
    """Model for storing user SMS preferences"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sms_preference')
    receive_match_notifications = models.BooleanField(default=True)
    receive_resource_updates = models.BooleanField(default=True)
    receive_campaign_updates = models.BooleanField(default=True)
    receive_feedback_notifications = models.BooleanField(default=True)
    receive_general_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return f"SMS Preferences for {self.user.username}"

