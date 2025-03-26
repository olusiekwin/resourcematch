from django.contrib import admin
from .models import SmsLog, SmsTemplate

@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'truncated_message', 'status', 'sent_at', 'cost')
    list_filter = ('status', 'sent_at')
    search_fields = ('recipient', 'message')
    readonly_fields = ('recipient', 'message', 'status', 'message_id', 'cost', 'sent_at')
    
    def truncated_message(self, obj):
        if len(obj.message) > 50:
            return f"{obj.message[:50]}..."
        return obj.message
    truncated_message.short_description = 'Message'

@admin.register(SmsTemplate)
class SmsTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_key', 'updated_at')
    search_fields = ('name', 'template_key', 'content')
    prepopulated_fields = {'template_key': ('name',)}

