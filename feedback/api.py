from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Feedback
from .serializers import FeedbackSerializer
from notifications.models import Notification

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Users can see feedback they've given or received
        return Feedback.objects.filter(
            models.Q(from_user=user) | models.Q(to_user=user)
        )
    
    def perform_create(self, serializer):
        feedback = serializer.save(from_user=self.request.user)
        
        # Create notification for the recipient
        Notification.objects.create(
            user=feedback.to_user,
            type='feedback_received',
            title='New Feedback Received',
            message=f'You received a {feedback.rating}-star rating from {feedback.from_user.username}.',
            related_object_type='feedback',
            related_object_id=feedback.id
        )

