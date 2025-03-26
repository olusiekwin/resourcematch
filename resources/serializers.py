from rest_framework import serializers
from .models import Resource, ResourceType

class ResourceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceType
        fields = ['id', 'name', 'description', 'icon']
        read_only_fields = ['id']

class ResourceSerializer(serializers.ModelSerializer):
    resource_type_name = serializers.CharField(source='resource_type.name', read_only=True)
    distance = serializers.FloatField(read_only=True, required=False)
    
    class Meta:
        model = Resource
        fields = ['id', 'resource_type', 'resource_type_name', 'name', 'description', 
                  'quantity', 'status', 'offered_by', 'requested_by', 
                  'latitude', 'longitude', 'created_at', 'updated_at', 'distance']
        read_only_fields = ['id', 'created_at', 'updated_at']

