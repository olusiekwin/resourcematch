from django.urls import path
from . import api

urlpatterns = [
    path('send/', api.send_sms_api, name='api_send_sms'),
    path('send-template/', api.send_template_sms_api, name='api_send_template_sms'),
    path('logs/', api.sms_logs_api, name='api_sms_logs'),
    path('templates/', api.sms_templates_api, name='api_sms_templates'),
]

