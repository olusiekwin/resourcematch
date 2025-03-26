from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.sms_dashboard, name='sms_dashboard'),
    path('logs/', views.sms_logs, name='sms_logs'),
    path('templates/', views.sms_templates, name='sms_templates'),
    path('templates/<int:template_id>/edit/', views.edit_template, name='edit_template'),
    path('templates/<int:template_id>/delete/', views.delete_template, name='delete_template'),
    path('send/', views.send_single_sms, name='send_single_sms'),
    path('send-bulk/', views.send_bulk_sms, name='send_bulk_sms'),
    path('send-template/', views.send_template, name='send_template'),
    path('callback/', views.africas_talking_callback, name='africas_talking_callback'),
]

