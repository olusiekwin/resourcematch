from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from math import radians, cos, sin, asin, sqrt
from .models import Resource, ResourceType
from .serializers import ResourceSerializer, ResourceTypeSerializer

# Haversine formula to calculate distance between two points
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371  # Radius of earth in kilometers
    return c * r

class ResourceTypeViewSet(viewsets.ModelViewSet):
    queryset = ResourceType.objects.all()
    serializer_class = ResourceTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Resource.objects.all()
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by resource type
        resource_type = self.request.query_params.get('type')
        if resource_type:
            queryset = queryset.filter(resource_type__name=resource_type)
        
        # If beneficiary, show only their requests and available resources
        if user.user_type == 'beneficiary':
            beneficiary = user.beneficiary_profile
            return queryset.filter(
                models.Q(requested_by=beneficiary) | 
                models.Q(status='available')
            )
        
        # If volunteer, show their offered resources and available requests
        elif user.user_type == 'volunteer':
            volunteer = user.volunteer_profile
            return queryset.filter(
                models.Q(offered_by=volunteer) | 
                models.Q(status='requested')
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find resources near a specific location"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        distance_km = float(request.query_params.get('distance', 10))
        status = request.query_params.get('status', 'available')
        
        if not (lat and lng):
            return Response({"error": "Latitude and longitude are required"}, status=400)
        
        try:
            lat = float(lat)
            lng = float(lng)
            
            # Get resources with the specified status
            resources = Resource.objects.filter(status=status)
            nearby_resources = []
            
            # Filter by distance
            for resource in resources:
                if resource.latitude and resource.longitude:
                    distance = haversine(lng, lat, resource.longitude, resource.latitude)
                    if distance <= distance_km:
                        resource.distance = distance  # Add distance attribute
                        nearby_resources.append(resource)
            
            # Sort by distance
            nearby_resources.sort(key=lambda x: x.distance)
            
            serializer = self.get_serializer(nearby_resources, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({"error": "Invalid coordinates"}, status=400)

