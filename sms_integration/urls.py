from django.urls import path
from . import views

urlpatterns = [
    path('sms/preferences/', views.sms_preferences, name='sms_preferences'),
    path('sms/callback/', views.africastalking_callback, name='africastalking_callback'),
    path('sms/incoming/', views.incoming_sms, name='incoming_sms'),
]

