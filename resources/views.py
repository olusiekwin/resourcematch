from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Resource, ResourceType, ResourceCategory
from .forms import (ResourceForm, ResourceRequestForm, ResourceOfferForm, 
                   ResourceTypeForm, ResourceCategoryForm, ResourceSearchForm)
from accounts.models import Beneficiary, Volunteer
from notifications.utils import create_notification
from sms_integration.utils import send_resource_notification

def home(request):
    # For the homepage we'll show some statistics and featured resources
    recent_resources = Resource.objects.filter(
        status__in=['available', 'requested']
    ).order_by('-created_at')[:6]
    
    # Get counts for dashboard stats
    resources_count = Resource.objects.count()
    available_count = Resource.objects.filter(status='available').count()
    requested_count = Resource.objects.filter(status='requested').count()
    matched_count = Resource.objects.filter(status__in=['matched', 'in_transit']).count()
    completed_count = Resource.objects.filter(status='completed').count()
    
    # Get resource types with counts
    resource_types = ResourceType.objects.annotate(
        resource_count=Count('resources')
    ).order_by('-resource_count')[:6]
    
    # Get categories with counts
    categories = ResourceCategory.objects.annotate(
        resource_count=Count('resources')
    ).order_by('-resource_count')[:4]
    
    return render(request, 'home.html', {
        'recent_resources': recent_resources,
        'resources_count': resources_count,
        'available_count': available_count,
        'requested_count': requested_count,
        'matched_count': matched_count,
        'completed_count': completed_count,
        'resource_types': resource_types,
        'categories': categories,
        'stats': {
            'beneficiaries_count': Beneficiary.objects.count(),
            'volunteers_count': Volunteer.objects.count(),
            'resources_count': completed_count,
            'donations_amount': "KSh 248,500"  # Example amount
        }
    })

def resource_list(request):
    """View for listing resources with filters"""
    # Initialize the search form
    form = ResourceSearchForm(request.GET)
    
    # Base queryset
    resources = Resource.objects.all()
    
    # Apply filters
    if form.is_valid():
        # Search query filter
        q = form.cleaned_data.get('q')
        if q:
            resources = resources.filter(
                Q(title__icontains=q) | 
                Q(description__icontains=q) |
                Q(resource_type__name__icontains=q)
            )
        
        # Resource type filter
        resource_type = form.cleaned_data.get('resource_type')
        if resource_type:
            resources = resources.filter(resource_type=resource_type)
        
        # Category filter
        category = form.cleaned_data.get('category')
        if category:
            resources = resources.filter(category=category)
        
        # Status filter
        status = form.cleaned_data.get('status')
        if status:
            resources = resources.filter(status=status)
        
        # Sorting
        sort = form.cleaned_data.get('sort', 'newest')
        if sort == 'newest':
            resources = resources.order_by('-created_at')
        elif sort == 'oldest':
            resources = resources.order_by('created_at')
        elif sort == 'name_asc':
            resources = resources.order_by('title')
        elif sort == 'name_desc':
            resources = resources.order_by('-title')
    else:
        # Default sorting by newest
        resources = resources.order_by('-created_at')
    
    # User-specific filtering
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        if request.user.userprofile.user_type == 'beneficiary':
            beneficiary = request.user.beneficiary_profile
            resources = resources.filter(
                Q(requested_by=beneficiary) | 
                Q(status='available')
            )
        elif request.user.userprofile.user_type == 'volunteer':
            volunteer = request.user.volunteer_profile
            resources = resources.filter(
                Q(offered_by=volunteer) | 
                Q(status='requested')
            )
    
    # Pagination
    paginator = Paginator(resources, 12)  # Show 12 resources per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all resource types and categories for filter dropdown
    resource_types = ResourceType.objects.all()
    resource_categories = ResourceCategory.objects.all()
    
    # Get resource counts by status for dashboard stats
    status_counts = Resource.objects.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_counts}
    
    context = {
        'resources': page_obj,
        'form': form,
        'resource_types': resource_types,
        'resource_categories': resource_categories,
        'status_counts': status_dict
    }
    
    return render(request, 'resources/resource_list.html', context)

@login_required
def resource_detail(request, resource_id):
    """View for showing resource details"""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if there's a match for this resource
    match = None
    try:
        match = resource.match
    except:
        pass
    
    # Check if the user has already given feedback for this match
    has_feedback = False
    if match and match.status == 'completed' and request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        if request.user.userprofile.user_type == 'beneficiary':
            has_feedback = match.feedbacks.filter(is_from_beneficiary=True).exists()
        elif request.user.userprofile.user_type == 'volunteer':
            has_feedback = match.feedbacks.filter(is_from_beneficiary=False).exists()
    
    # Get similar resources
    similar_resources = Resource.objects.filter(
        resource_type=resource.resource_type,
        status=resource.status
    ).exclude(id=resource.id)[:3]
    
    # Track resource view if not already viewed in this session
    if not request.session.get(f'viewed_resource_{resource_id}'):
        resource.view_count += 1
        resource.save()
        request.session[f'viewed_resource_{resource_id}'] = True
    
    # Check if user can request/offer this resource
    can_request = False
    can_offer = False
    
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        if request.user.userprofile.user_type == 'beneficiary' and resource.status == 'available':
            can_request = True
        elif request.user.userprofile.user_type == 'volunteer' and resource.status == 'requested':
            can_offer = True
    
    context = {
        'resource': resource,
        'match': match,
        'has_feedback': has_feedback,
        'similar_resources': similar_resources,
        'can_request': can_request,
        'can_offer': can_offer
    }
    
    return render(request, 'resources/resource_detail.html', context)

@login_required
def request_resource(request):
    """View for beneficiaries to request resources"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'beneficiary':
        messages.error(request, 'Only beneficiaries can request resources.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        form = ResourceRequestForm(request.POST, request.FILES, beneficiary=request.user.beneficiary_profile)
        if form.is_valid():
            resource = form.save()
            
            # Create notification for admin
            create_notification(
                recipient=None,  # Admin notification
                title="New Resource Request",
                message=f"A new resource has been requested: {resource.title}",
                link=f"/resources/{resource.id}/",
                is_admin=True
            )
            
            # Send SMS notification to volunteers near the location
            send_resource_notification(resource, 'new_request')
            
            messages.success(request, 'Resource request created successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceRequestForm(beneficiary=request.user.beneficiary_profile)
    
    context = {
        'form': form,
        'resource_types': ResourceType.objects.all(),
        'resource_categories': ResourceCategory.objects.all()
    }
    
    return render(request, 'resources/request_resource.html', context)

@login_required
def offer_resource(request):
    """View for volunteers to offer resources"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'volunteer':
        messages.error(request, 'Only volunteers can offer resources.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        form = ResourceOfferForm(request.POST, request.FILES, volunteer=request.user.volunteer_profile)
        if form.is_valid():
            resource = form.save()
            
            # Create notification for admin
            create_notification(
                recipient=None,  # Admin notification
                title="New Resource Offer",
                message=f"A new resource has been offered: {resource.title}",
                link=f"/resources/{resource.id}/",
                is_admin=True
            )
            
            # Send SMS notification to beneficiaries who might need this resource
            send_resource_notification(resource, 'new_offer')
            
            messages.success(request, 'Resource offer created successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceOfferForm(volunteer=request.user.volunteer_profile)
    
    context = {
        'form': form,
        'resource_types': ResourceType.objects.all(),
        'resource_categories': ResourceCategory.objects.all()
    }
    
    return render(request, 'resources/offer_resource.html', context)

@login_required
def edit_resource(request, resource_id):
    """View for editing resources"""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user has permission to edit this resource
    has_permission = False
    if request.user.is_staff:
        has_permission = True
    elif hasattr(request.user, 'userprofile'):
        if request.user.userprofile.user_type == 'beneficiary' and resource.requested_by == request.user.beneficiary_profile:
            has_permission = True
        elif request.user.userprofile.user_type == 'volunteer' and resource.offered_by == request.user.volunteer_profile:
            has_permission = True
    
    if not has_permission:
        messages.error(request, 'You do not have permission to edit this resource.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            updated_resource = form.save()
            updated_resource.updated_at = timezone.now()
            updated_resource.save()
            
            messages.success(request, 'Resource updated successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceForm(instance=resource)
    
    context = {
        'form': form, 
        'resource': resource,
        'resource_types': ResourceType.objects.all(),
        'resource_categories': ResourceCategory.objects.all()
    }
    
    return render(request, 'resources/edit_resource.html', context)

@login_required
def cancel_resource(request, resource_id):
    """View for cancelling resources"""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user has permission to cancel this resource
    has_permission = False
    if request.user.is_staff:
        has_permission = True
    elif hasattr(request.user, 'userprofile'):
        if request.user.userprofile.user_type == 'beneficiary' and resource.requested_by == request.user.beneficiary_profile:
            has_permission = True
        elif request.user.userprofile.user_type == 'volunteer' and resource.offered_by == request.user.volunteer_profile:
            has_permission = True
    
    if not has_permission:
        messages.error(request, 'You do not have permission to cancel this resource.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        resource.status = 'cancelled'
        resource.updated_at = timezone.now()
        resource.save()
        
        # Create notification for interested parties
        if resource.requested_by:
            create_notification(
                recipient=resource.requested_by.user,
                title="Resource Cancelled",
                message=f"The resource '{resource.title}' has been cancelled.",
                link=f"/resources/{resource.id}/"
            )
        
        if resource.offered_by:
            create_notification(
                recipient=resource.offered_by.user,
                title="Resource Cancelled",
                message=f"The resource '{resource.title}' has been cancelled.",
                link=f"/resources/{resource.id}/"
            )
        
        messages.success(request, 'Resource cancelled successfully.')
        return redirect('resource_list')
    
    return render(request, 'resources/cancel_resource.html', {'resource': resource})

def resource_map(request):
    """View for displaying resources on a map"""
    # Get resources with location data
    resources = Resource.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    # Filter based on status if provided
    status = request.GET.get('status')
    if status:
        resources = resources.filter(status=status)
    
    # Filter based on user type
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        if request.user.userprofile.user_type == 'beneficiary':
            beneficiary = request.user.beneficiary_profile
            resources = resources.filter(
                Q(requested_by=beneficiary) | 
                Q(status='available')
            )
        elif request.user.userprofile.user_type == 'volunteer':
            volunteer = request.user.volunteer_profile
            resources = resources.filter(
                Q(offered_by=volunteer) | 
                Q(status='requested')
            )
    
    # Get all resource types and categories for filter
    resource_types = ResourceType.objects.all()
    resource_categories = ResourceCategory.objects.all()
    
    # Prepare resource data for map
    resource_data = []
    for resource in resources:
        resource_data.append({
            'id': resource.id,
            'title': resource.title,
            'type': resource.resource_type.name,
            'category': resource.category.name if resource.category else '',
            'status': resource.get_status_display(),
            'latitude': float(resource.latitude),
            'longitude': float(resource.longitude),
            'url': f'/resources/{resource.id}/'
        })
    
    context = {
        'resources': resources,
        'resource_types': resource_types,
        'resource_categories': resource_categories,
        'resource_data_json': resource_data,
        'selected_status': status
    }
    
    return render(request, 'resources/resource_map.html', context)

def beneficiary_categories(request):
    """View for displaying beneficiary categories"""
    categories = ResourceCategory.objects.all()
    
    # Get some stats for each category
    for category in categories:
        category.resource_count = Resource.objects.filter(category=category).count()
        category.available_count = Resource.objects.filter(category=category, status='available').count()
        category.requested_count = Resource.objects.filter(category=category, status='requested').count()
    
    return render(request, 'resources/beneficiary_categories.html', {
        'categories': categories
    })

# API endpoints
def resource_search_api(request):
    """API endpoint for searching resources via AJAX"""
    search_query = request.GET.get('q', '')
    resource_type = request.GET.get('type')
    category = request.GET.get('category')
    
    resources = Resource.objects.filter(
        Q(title__icontains=search_query) | 
        Q(description__icontains=search_query)
    )
    
    if resource_type:
        resources = resources.filter(resource_type__id=resource_type)
    
    if category:
        resources = resources.filter(category__id=category)
    
    results = []
    for resource in resources[:10]:  # Limit to 10 results
        results.append({
            'id': resource.id,
            'title': resource.title,
            'type': resource.resource_type.name,
            'status': resource.get_status_display(),
            'url': f'/resources/{resource.id}/'
        })
    
    return JsonResponse({'results': results})

