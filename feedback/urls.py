from django.urls import path
from . import views

urlpatterns = [
    path('feedback/', views.feedback_list, name='feedback_list'),
    path('feedback/create/', views.create_feedback, name='create_feedback'),
    path('feedback/<int:feedback_id>/', views.feedback_detail, name='feedback_detail'),
]

