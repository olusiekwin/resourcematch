from django.urls import path
from . import views

urlpatterns = [
    # Campaign URLs
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('campaigns/create/', views.create_campaign, name='create_campaign'),
    path('campaigns/<int:campaign_id>/edit/', views.edit_campaign, name='edit_campaign'),
    path('campaigns/<int:campaign_id>/update/', views.add_campaign_update, name='add_campaign_update'),
    
    # Donation URLs
    path('campaigns/<int:campaign_id>/donate/', views.make_donation, name='make_donation'),
    path('donations/<int:donation_id>/success/', views.donation_success, name='donation_success'),
    path('donations/<int:donation_id>/', views.donation_detail, name='donation_detail'),
    path('donations/<int:donation_id>/receipt/', views.download_receipt, name='download_receipt'),
    
    # Dashboard URL
    path('dashboard/donor/', views.donor_dashboard, name='donor_dashboard'),
    
    # Beneficiary categories
    path('beneficiary-categories/', views.beneficiary_categories, name='beneficiary_categories'),
]

