from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Resource, ResourceType
from .forms import ResourceForm, ResourceRequestForm, ResourceOfferForm, ResourceTypeForm

@login_required
def resource_list(request):
    user = request.user
    
    # Get filter parameters
    status = request.GET.get('status')
    resource_type = request.GET.get('type')
    
    # Base queryset
    resources = Resource.objects.all()
    
    # Apply filters
    if status:
        resources = resources.filter(status=status)
    
    if resource_type:
        resources = resources.filter(resource_type__name=resource_type)
    
    # Filter based on user type
    if user.user_type == 'beneficiary':
        beneficiary = user.beneficiary_profile
        resources = resources.filter(
            Q(requested_by=beneficiary) | 
            Q(status='available')
        )
    elif user.user_type == 'volunteer':
        volunteer = user.volunteer_profile
        resources = resources.filter(
            Q(offered_by=volunteer) | 
            Q(status='requested')
        )
    
    # Get all resource types for filter dropdown
    resource_types = ResourceType.objects.all()
    
    return render(request, 'resources/resource_list.html', {
        'resources': resources,
        'resource_types': resource_types,
        'selected_status': status,
        'selected_type': resource_type
    })

@login_required
def resource_detail(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if there's a match for this resource
    match = None
    if hasattr(resource, 'match'):
        match = resource.match
    
    # Check if the user has already given feedback for this match
    has_feedback = False
    if match and match.status == 'completed':
        if request.user.user_type == 'beneficiary':
            has_feedback = match.beneficiary_feedback is not None
        elif request.user.user_type == 'volunteer':
            has_feedback = match.volunteer_feedback is not None
    
    return render(request, 'resources/resource_detail.html', {
        'resource': resource,
        'match': match,
        'has_feedback': has_feedback
    })

@login_required
def request_resource(request):
    if request.user.user_type != 'beneficiary':
        messages.error(request, 'Only beneficiaries can request resources.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        form = ResourceRequestForm(request.POST, beneficiary=request.user.beneficiary_profile)
        if form.is_valid():
            resource = form.save()
            messages.success(request, 'Resource request created successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceRequestForm(beneficiary=request.user.beneficiary_profile)
    
    return render(request, 'resources/request_resource.html', {'form': form})

@login_required
def offer_resource(request):
    if request.user.user_type != 'volunteer':
        messages.error(request, 'Only volunteers can offer resources.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        form = ResourceOfferForm(request.POST, volunteer=request.user.volunteer_profile)
        if form.is_valid():
            resource = form.save()
            messages.success(request, 'Resource offer created successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceOfferForm(volunteer=request.user.volunteer_profile)
    
    return render(request, 'resources/offer_resource.html', {'form': form})

@login_required
def edit_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user has permission to edit this resource
    if request.user.user_type == 'beneficiary' and resource.requested_by != request.user.beneficiary_profile:
        messages.error(request, 'You do not have permission to edit this resource.')
        return redirect('resource_list')
    
    if request.user.user_type == 'volunteer' and resource.offered_by != request.user.volunteer_profile:
        messages.error(request, 'You do not have permission to edit this resource.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resource updated successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceForm(instance=resource)
    
    return render(request, 'resources/edit_resource.html', {'form': form, 'resource': resource})

@login_required
def cancel_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user has permission to cancel this resource
    if request.user.user_type == 'beneficiary' and resource.requested_by != request.user.beneficiary_profile:
        messages.error(request, 'You do not have permission to cancel this resource.')
        return redirect('resource_list')
    
    if request.user.user_type == 'volunteer' and resource.offered_by != request.user.volunteer_profile:
        messages.error(request, 'You do not have permission to cancel this resource.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        resource.status = 'cancelled'
        resource.save()
        messages.success(request, 'Resource cancelled successfully.')
        return redirect('resource_list')
    
    return redirect('resource_detail', resource_id=resource.id)

@login_required
def resource_type_list(request):
    resource_types = ResourceType.objects.all()
    return render(request, 'resources/resource_type_list.html', {'resource_types': resource_types})

@login_required
def resource_type_detail(request, type_id):
    resource_type = get_object_or_404(ResourceType, id=type_id)
    resources = Resource.objects.filter(resource_type=resource_type)
    
    return render(request, 'resources/resource_type_detail.html', {
        'resource_type': resource_type,
        'resources': resources
    })

@login_required
def resource_map(request):
    # Get resources with location data
    resources = Resource.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    # Filter based on user type
    user = request.user
    if user.user_type == 'beneficiary':
        beneficiary = user.beneficiary_profile
        resources = resources.filter(
            Q(requested_by=beneficiary) | 
            Q(status='available')
        )
    elif user.user_type == 'volunteer':
        volunteer = user.volunteer_profile
        resources = resources.filter(
            Q(offered_by=volunteer) | 
            Q(status='requested')
        )
    
    return render(request, 'resources/resource_map.html', {'resources': resources})

