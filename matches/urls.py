from django.urls import path
from . import views

urlpatterns = [
    path('', views.match_list, name='match_list'),
    path('<int:match_id>/', views.match_detail, name='match_detail'),
    path('create/<int:resource_id>/', views.create_match, name='create_match'),
    path('<int:match_id>/accept/', views.accept_match, name='accept_match'),
    path('<int:match_id>/complete/', views.complete_match, name='complete_match'),
    path('<int:match_id>/cancel/', views.cancel_match, name='cancel_match'),
    path('<int:match_id>/feedback/', views.give_feedback, name='give_feedback'),
    path('volunteer/<int:resource_id>/', views.volunteer_match, name='volunteer_match'),
]

