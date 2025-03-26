from rest_framework import serializers
from .models import User, Beneficiary, Volunteer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'user_type', 'phone_number', 'address', 'latitude', 'longitude']
        read_only_fields = ['id']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class BeneficiarySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Beneficiary
        fields = ['id', 'user', 'needs_description', 'emergency_contact_name', 
                  'emergency_contact_phone', 'mobility_limitations']
        read_only_fields = ['id']

class VolunteerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    distance = serializers.FloatField(read_only=True, required=False)
    
    class Meta:
        model = Volunteer
        fields = ['id', 'user', 'bio', 'availability', 'transportation_type', 
                  'verified', 'active', 'max_distance_km', 'distance']
        read_only_fields = ['id', 'verified']

