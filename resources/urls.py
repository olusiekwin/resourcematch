from django.urls import path
from . import views

urlpatterns = [
    path('', views.resource_list, name='resource_list'),
    path('<int:resource_id>/', views.resource_detail, name='resource_detail'),
    path('request/', views.request_resource, name='request_resource'),
    path('offer/', views.offer_resource, name='offer_resource'),
    path('<int:resource_id>/edit/', views.edit_resource, name='edit_resource'),
    path('<int:resource_id>/cancel/', views.cancel_resource, name='cancel_resource'),
    path('<int:resource_id>/action/', views.resource_action, name='resource_action'),
    path('types/', views.resource_type_list, name='resource_type_list'),
    path('types/<int:type_id>/', views.resource_type_detail, name='resource_type_detail'),
    path('categories/', views.resource_category_list, name='resource_category_list'),
    path('categories/<int:category_id>/', views.resource_category_detail, name='resource_category_detail'),
    path('map/', views.resource_map, name='resource_map'),
    path('beneficiary-categories/', views.beneficiary_categories, name='beneficiary_categories'),
    path('search/', views.search_resources, name='search_resources'),
]

