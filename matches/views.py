from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Match, Feedback
from .forms import MatchForm, FeedbackForm
from resources.models import Resource
from notifications.utils import create_notification

@login_required
def match_list(request):
    user = request.user
    
    if hasattr(user, 'userprofile'):
        if user.userprofile.user_type == 'beneficiary':
            matches = Match.objects.filter(beneficiary=user.beneficiary_profile)
        elif user.userprofile.user_type == 'volunteer':
            matches = Match.objects.filter(volunteer=user.volunteer_profile)
        else:  # Admin or donor
            matches = Match.objects.all()
    else:
        matches = Match.objects.none()
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        matches = matches.filter(status=status)
    
    return render(request, 'matches/match_list.html', {
        'matches': matches,
        'selected_status': status
    })

@login_required
def match_detail(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    # Check if user has permission to view this match
    user = request.user
    if (hasattr(user, 'userprofile') and 
        user.userprofile.user_type == 'beneficiary' and 
        match.beneficiary  and 
        user.userprofile.user_type == 'beneficiary' and 
        match.beneficiary != user.beneficiary_profile):
        messages.error(request, 'You do not have permission to view this match.')
        return redirect('match_list')
    
    if (hasattr(user, 'userprofile') and 
        user.userprofile.user_type == 'volunteer' and 
        match.volunteer != user.volunteer_profile):
        messages.error(request, 'You do not have permission to view this match.')
        return redirect('match_list')
    
    # Check if the user has already given feedback
    has_feedback = False
    if match.status == 'completed':
        if hasattr(user, 'userprofile'):
            if user.userprofile.user_type == 'beneficiary':
                has_feedback = match.feedbacks.filter(is_from_beneficiary=True).exists()
            elif user.userprofile.user_type == 'volunteer':
                has_feedback = match.feedbacks.filter(is_from_beneficiary=False).exists()
    
    return render(request, 'matches/match_detail.html', {
        'match': match,
        'has_feedback': has_feedback
    })

@login_required
def create_match(request, resource_id):
    # Only admins can manually create matches
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to create matches.')
        return redirect('resource_list')
    
    resource = get_object_or_404(Resource, id=resource_id)
    
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            match = form.save(commit=False)
            match.resource = resource
            match.beneficiary = resource.requested_by
            match.volunteer = resource.offered_by
            match.save()
            
            # Update resource status
            resource.status = 'in_transit'
            resource.save()
            
            # Create notifications
            create_notification(
                recipient=match.beneficiary.user,
                title='New Match Created',
                message=f'Your resource request "{resource.name}" has been matched with a volunteer.',
                link=f'/matches/{match.id}/'
            )
            
            create_notification(
                recipient=match.volunteer.user,
                title='New Match Created',
                message=f'You have been matched to provide "{resource.name}" to a beneficiary.',
                link=f'/matches/{match.id}/'
            )
            
            messages.success(request, 'Match created successfully.')
            return redirect('match_detail', match_id=match.id)
    else:
        form = MatchForm()
    
    return render(request, 'matches/create_match.html', {
        'form': form,
        'resource': resource
    })

@login_required
def volunteer_match(request, resource_id):
    # Only volunteers can volunteer for matches
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'volunteer':
        messages.error(request, 'Only volunteers can volunteer for matches.')
        return redirect('resource_list')
    
    resource = get_object_or_404(Resource, id=resource_id, status='requested')
    volunteer = request.user.volunteer_profile
    
    if request.method == 'POST':
        # Create the match
        match = Match.objects.create(
            resource=resource,
            beneficiary=resource.requested_by,
            volunteer=volunteer,
            status='pending'
        )
        
        # Update resource status
        resource.status = 'in_transit'
        resource.save()
        
        # Create notifications
        create_notification(
            recipient=match.beneficiary.user,
            title='Volunteer Found',
            message=f'A volunteer has offered to help with your request "{resource.name}".',
            link=f'/matches/{match.id}/'
        )
        
        messages.success(request, 'You have volunteered to help with this request.')
        return redirect('match_detail', match_id=match.id)
    
    return redirect('resource_detail', resource_id=resource_id)

@login_required
def accept_match(request, match_id):
    match = get_object_or_404(Match, id=match_id, status='pending')
    
    # Only the volunteer can accept a match
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'volunteer' or match.volunteer != request.user.volunteer_profile:
        messages.error(request, 'You do not have permission to accept this match.')
        return redirect('match_list')
    
    if request.method == 'POST':
        match.status = 'accepted'
        match.save()
        
        # Create notification for beneficiary
        create_notification(
            recipient=match.beneficiary.user,
            title='Match Accepted',
            message=f'The volunteer has accepted the match for "{match.resource.name}".',
            link=f'/matches/{match.id}/'
        )
        
        messages.success(request, 'Match accepted successfully.')
    
    return redirect('match_detail', match_id=match.id)

@login_required
def complete_match(request, match_id):
    match = get_object_or_404(Match, id=match_id, status='accepted')
    
    # Only the volunteer can mark a match as completed
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'volunteer' or match.volunteer != request.user.volunteer_profile:
        messages.error(request, 'You do not have permission to complete this match.')
        return redirect('match_list')
    
    if request.method == 'POST':
        match.status = 'completed'
        match.save()
        
        # Update resource status
        resource = match.resource
        resource.status = 'delivered'
        resource.save()
        
        # Create notification for beneficiary
        create_notification(
            recipient=match.beneficiary.user,
            title='Match Completed',
            message=f'The volunteer has marked the match for "{match.resource.name}" as completed. Please provide feedback.',
            link=f'/matches/{match.id}/feedback/'
        )
        
        messages.success(request, 'Match marked as completed.')
    
    return redirect('match_detail', match_id=match.id)

@login_required
def cancel_match(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    # Check if user has permission to cancel this match
    user = request.user
    if (hasattr(user, 'userprofile') and 
        user.userprofile.user_type == 'beneficiary' and 
        match.beneficiary != user.beneficiary_profile):
        messages.error(request, 'You do not have permission to cancel this match.')
        return redirect('match_list')
    
    if (hasattr(user, 'userprofile') and 
        user.userprofile.user_type == 'volunteer' and 
        match.volunteer != user.volunteer_profile):
        messages.error(request, 'You do not have permission to cancel this match.')
        return redirect('match_list')
    
    if request.method == 'POST':
        match.status = 'cancelled'
        match.save()
        
        # Update resource status
        resource = match.resource
        if hasattr(user, 'userprofile') and user.userprofile.user_type == 'beneficiary':
            resource.status = 'cancelled'
        else:
            resource.status = 'requested'  # Reset to requested so another volunteer can help
        resource.save()
        
        # Create notification for the other party
        if hasattr(user, 'userprofile') and user.userprofile.user_type == 'beneficiary':
            create_notification(
                recipient=match.volunteer.user,
                title='Match Cancelled',
                message=f'The beneficiary has cancelled the match for "{match.resource.name}".',
                link=f'/matches/{match.id}/'
            )
        else:
            create_notification(
                recipient=match.beneficiary.user,
                title='Match Cancelled',
                message=f'The volunteer has cancelled the match for "{match.resource.name}".',
                link=f'/matches/{match.id}/'
            )
        
        messages.success(request, 'Match cancelled successfully.')
    
    return redirect('match_detail', match_id=match.id)

@login_required
def give_feedback(request, match_id):
    match = get_object_or_404(Match, id=match_id, status='completed')
    
    # Check if user has permission to give feedback for this match
    user = request.user
    if (hasattr(user, 'userprofile') and 
        user.userprofile.user_type == 'beneficiary' and 
        match.beneficiary != user.beneficiary_profile):
        messages.error(request, 'You do not have permission to give feedback for this match.')
        return redirect('match_list')
    
    if (hasattr(user, 'userprofile') and 
        user.userprofile.user_type == 'volunteer' and 
        match.volunteer != user.volunteer_profile):
        messages.error(request, 'You do not have permission to give feedback for this match.')
        return redirect('match_list')
    
    # Check if the user has already given feedback
    is_from_beneficiary = (hasattr(user, 'userprofile') and user.userprofile.user_type == 'beneficiary')
    existing_feedback = match.feedbacks.filter(is_from_beneficiary=is_from_beneficiary).first()
    
    if existing_feedback:
        messages.info(request, 'You have already provided feedback for this match.')
        return redirect('match_detail', match_id=match.id)
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.match = match
            feedback.is_from_beneficiary = is_from_beneficiary
            feedback.save()
            
            # Create notification for the other party
            if is_from_beneficiary:
                create_notification(
                    recipient=match.volunteer.user,
                    title='New Feedback Received',
                    message=f'The beneficiary has provided feedback for the match "{match.resource.name}".',
                    link=f'/matches/{match.id}/'
                )
            else:
                create_notification(
                    recipient=match.beneficiary.user,
                    title='New Feedback Received',
                    message=f'The volunteer has provided feedback for the match "{match.resource.name}".',
                    link=f'/matches/{match.id}/'
                )
            
            messages.success(request, 'Feedback submitted successfully.')
            return redirect('match_detail', match_id=match.id)
    else:
        form = FeedbackForm()
    
    return render(request, 'matches/give_feedback.html', {
        'form': form,
        'match': match
    })

