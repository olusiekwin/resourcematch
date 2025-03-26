from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Beneficiary, Volunteer

class UserSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(source='userprofile.user_type', read_only=True)
    phone_number = serializers.CharField(source='userprofile.phone_number', required=False)
    address = serializers.CharField(source='userprofile.address', required=False)
    latitude = serializers.FloatField(source='userprofile.latitude', required=False)
    longitude = serializers.FloatField(source='userprofile.longitude', required=False)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'user_type', 'phone_number', 'address', 'latitude', 'longitude']
        read_only_fields = ['id']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        profile_data = validated_data.pop('userprofile', {})
        user = User.objects.create_user(**validated_data)
        
        # Update profile
        profile = user.userprofile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        
        return user
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('userprofile', {})
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile
        profile = instance.userprofile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        
        return instance

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

