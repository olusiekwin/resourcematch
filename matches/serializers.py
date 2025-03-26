from rest_framework import serializers
from .models import Match
from accounts.serializers import BeneficiarySerializer, VolunteerSerializer
from resources.serializers import ResourceSerializer

class MatchSerializer(serializers.ModelSerializer):
    beneficiary_details = BeneficiarySerializer(source='beneficiary', read_only=True)
    volunteer_details = VolunteerSerializer(source='volunteer', read_only=True)
    resource_details = ResourceSerializer(source='resource', read_only=True)
    
    class Meta:
        model = Match
        fields = ['id', 'beneficiary', 'volunteer', 'resource', 
                  'beneficiary_details', 'volunteer_details', 'resource_details',
                  'status', 'created_at', 'notes', 'estimated_arrival']
        read_only_fields = ['id', 'created_at']

