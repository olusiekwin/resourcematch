from django.db import models
from django.conf import settings
from django.utils import timezone

class SmsLog(models.Model):
    """Model to log all SMS messages sent through the system"""
    recipient = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=50)
    message_id = models.CharField(max_length=100, blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sent_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'SMS Log'
        verbose_name_plural = 'SMS Logs'
    
    def __str__(self):
        return f"SMS to {self.recipient} on {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

class SmsTemplate(models.Model):
    """Model for predefined SMS templates"""
    name = models.CharField(max_length=100)
    template_key = models.SlugField(unique=True)
    content = models.TextField(help_text="Use {variable} syntax for placeholders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'SMS Template'
        verbose_name_plural = 'SMS Templates'
    
    def __str__(self):
        return self.name

