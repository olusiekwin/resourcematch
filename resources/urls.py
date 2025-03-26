from django.urls import path
from . import views

urlpatterns = [
    # Main resource views
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/<int:resource_id>/', views.resource_detail, name='resource_detail'),
    path('resources/request/', views.request_resource, name='request_resource'),
    path('resources/offer/', views.offer_resource, name='offer_resource'),
    path('resources/<int:resource_id>/edit/', views.edit_resource, name='edit_resource'),
    path('resources/<int:resource_id>/cancel/', views.cancel_resource, name='cancel_resource'),
    
    # Map view
    path('resources/map/', views.resource_map, name='resource_map'),
    
    # Categories and types
    path('beneficiary-categories/', views.beneficiary_categories, name='beneficiary_categories'),
    
    # API endpoints
    path('api/resources/search/', views.resource_search_api, name='resource_search_api'),
]

