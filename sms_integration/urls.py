from django.urls import path
from . import views

urlpatterns = [
    path('sms/preferences/', views.sms_preferences, name='sms_preferences'),
    path('sms/webhook/', views.twilio_webhook, name='twilio_webhook'),
]

