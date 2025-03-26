from rest_framework import serializers
from .models import Feedback
from accounts.serializers import UserSerializer

class FeedbackSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Feedback
        fields = ['id', 'user', 'user_details', 'title', 'content', 'rating', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

