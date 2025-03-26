from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Match
from .serializers import MatchSerializer
from notifications.utils import create_notification

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # If beneficiary, show only their matches
        if hasattr(user, 'userprofile') and user.userprofile.user_type == 'beneficiary':
            beneficiary = user.beneficiary_profile
            return Match.objects.filter(beneficiary=beneficiary)
        
        # If volunteer, show only their matches
        elif hasattr(user, 'userprofile') and user.userprofile.user_type == 'volunteer':
            volunteer = user.volunteer_profile
            return Match.objects.filter(volunteer=volunteer)
        
        return super().get_queryset()
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        match = self.get_object()
        
        # Only the volunteer can accept a match
        if (not hasattr(request.user, 'userprofile') or 
            request.user.userprofile.user_type != 'volunteer' or 
            request.user.volunteer_profile != match.volunteer):
            return Response({"error": "Only the assigned volunteer can accept this match"}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        if match.status != 'pending':
            return Response({"error": "This match is not in pending status"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        match.status = 'accepted'
        match.save()
        
        # Update resource status
        resource = match.resource
        resource.status = 'in_transit'
        resource.save()
        
        # Create notification for beneficiary
        create_notification(
            recipient=match.beneficiary.user,
            title='Match Accepted',
            message=f'Your resource request for {resource.name} has been accepted by a volunteer.',
            link=f'/matches/{match.id}/'
        )
        
        serializer = self.get_serializer(match)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        match = self.get_object()
        
        # Only the volunteer can complete a match
        if (not hasattr(request.user, 'userprofile') or 
            request.user.userprofile.user_type != 'volunteer' or 
            request.user.volunteer_profile != match.volunteer):
            return Response({"error": "Only the assigned volunteer can complete this match"}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        if match.status != 'accepted' and match.status != 'in_progress':
            return Response({"error": "This match must be accepted or in progress to be completed"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        match.status = 'completed'
        match.save()
        
        # Update resource status
        resource = match.resource
        resource.status = 'delivered'
        resource.save()
        
        # Create notification for beneficiary
        create_notification(
            recipient=match.beneficiary.user,
            title='Resource Delivered',
            message=f'Your resource request for {resource.name} has been delivered.',
            link=f'/matches/{match.id}/'
        )
        
        serializer = self.get_serializer(match)
        return Response(serializer.data)

