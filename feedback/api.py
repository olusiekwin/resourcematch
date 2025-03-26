from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db import models
from .models import Feedback
from .serializers import FeedbackSerializer
from notifications.utils import create_notification

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Users can see feedback they've given or received
        return Feedback.objects.filter(
            models.Q(user=user) | models.Q(match__beneficiary__user=user) | models.Q(match__volunteer__user=user)
        )
    
    def perform_create(self, serializer):
        feedback = serializer.save(user=self.request.user)
        
        # Create notification for the recipient
        if hasattr(feedback, 'match'):
            if feedback.is_from_beneficiary:
                recipient = feedback.match.volunteer.user
            else:
                recipient = feedback.match.beneficiary.user
                
            create_notification(
                recipient=recipient,
                title='New Feedback Received',
                message=f'You received a {feedback.rating}-star rating for a match.',
                link=f'/matches/{feedback.match.id}/'
            )

