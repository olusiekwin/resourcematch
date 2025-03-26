from django.urls import path
from . import views

urlpatterns = [
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/<int:resource_id>/', views.resource_detail, name='resource_detail'),
    path('resources/request/', views.request_resource, name='request_resource'),
    path('resources/offer/', views.offer_resource, name='offer_resource'),
    path('resources/<int:resource_id>/edit/', views.edit_resource, name='edit_resource'),
    path('resources/<int:resource_id>/cancel/', views.cancel_resource, name='cancel_resource'),
    path('resources/types/', views.resource_type_list, name='resource_type_list'),
    path('resources/types/<int:type_id>/', views.resource_type_detail, name='resource_type_detail'),
    path('resources/map/', views.resource_map, name='resource_map'),
]

