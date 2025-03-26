from django.urls import path
from . import views

urlpatterns = [
    path('', views.feedback_list, name='feedback_list'),
    path('create/', views.create_feedback, name='create_feedback'),
    path('<int:feedback_id>/', views.feedback_detail, name='feedback_detail'),
]

