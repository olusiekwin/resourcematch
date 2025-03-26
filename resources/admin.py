from django.contrib import admin
from .models import ResourceType, Resource

@admin.register(ResourceType)
class ResourceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource_type', 'status', 'quantity', 'offered_by', 'requested_by')
    list_filter = ('status', 'resource_type')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

