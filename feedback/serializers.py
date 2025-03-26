from rest_framework import serializers
from .models import Feedback
from accounts.serializers import UserSerializer

class FeedbackSerializer(serializers.ModelSerializer):
    from_user_details = UserSerializer(source='from_user', read_only=True)
    to_user_details = UserSerializer(source='to_user', read_only=True)
    
    class Meta:
        model = Feedback
        fields = ['id', 'match', 'from_user', 'to_user', 
                  'from_user_details', 'to_user_details',
                  'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'from_user', 'created_at']

