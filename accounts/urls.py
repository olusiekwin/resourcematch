from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('volunteers/', views.volunteer_list, name='volunteer_list'),
    path('volunteers/<int:volunteer_id>/', views.volunteer_detail, name='volunteer_detail'),
    path('beneficiaries/', views.beneficiary_list, name='beneficiary_list'),
    path('beneficiaries/<int:beneficiary_id>/', views.beneficiary_detail, name='beneficiary_detail'),
]

