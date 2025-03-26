from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from math import radians, cos, sin, asin, sqrt
from .models import User, Beneficiary, Volunteer
from .serializers import UserSerializer, BeneficiarySerializer, VolunteerSerializer

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

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        # Regular users can only see their own profile
        if not self.request.user.is_staff:
            return User.objects.filter(id=self.request.user.id)
        return super().get_queryset()

class BeneficiaryViewSet(viewsets.ModelViewSet):
    queryset = Beneficiary.objects.all()
    serializer_class = BeneficiarySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        # Volunteers can see all beneficiaries, beneficiaries can only see themselves
        user = self.request.user
        if user.user_type == 'beneficiary':
            return Beneficiary.objects.filter(user=user)
        return super().get_queryset()

class VolunteerViewSet(viewsets.ModelViewSet):
    queryset = Volunteer.objects.all()
    serializer_class = VolunteerSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find volunteers near a specific location"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        distance_km = float(request.query_params.get('distance', 10))
        
        if not (lat and lng):
            return Response({"error": "Latitude and longitude are required"}, status=400)
        
        try:
            lat = float(lat)
            lng = float(lng)
            
            # Get all active volunteers
            volunteers = Volunteer.objects.filter(active=True)
            nearby_volunteers = []
            
            # Filter by distance
            for volunteer in volunteers:
                if volunteer.user.latitude and volunteer.user.longitude:
                    distance = haversine(lng, lat, volunteer.user.longitude, volunteer.user.latitude)
                    if distance <= distance_km:
                        volunteer.distance = distance  # Add distance attribute
                        nearby_volunteers.append(volunteer)
            
            # Sort by distance
            nearby_volunteers.sort(key=lambda x: x.distance)
            
            serializer = self.get_serializer(nearby_volunteers, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({"error": "Invalid coordinates"}, status=400)

