from django.contrib import admin
from .models import SMSTemplate, SMSLog, SMSPreference

@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'template_text', 'description')

@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'phone_number', 'status', 'sent_at', 'delivered_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('recipient__user__username', 'phone_number', 'message')
    readonly_fields = ('sent_at', 'delivered_at', 'external_id')

@admin.register(SMSPreference)
class SMSPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'receive_match_notifications', 'receive_resource_updates', 'receive_campaign_updates')
    list_filter = ('receive_match_notifications', 'receive_resource_updates', 'receive_campaign_updates')
    search_fields = ('user__username', 'user__email')

