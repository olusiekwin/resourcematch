from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Resource, ResourceType, ResourceCategory
from .forms import ResourceForm, ResourceRequestForm, ResourceOfferForm, ResourceTypeForm
from accounts.models import UserProfile
from notifications.utils import create_notification

@login_required
def resource_list(request):
    user = request.user
    
    # Get filter parameters
    status = request.GET.get('status')
    resource_type = request.GET.get('type')
    category = request.GET.get('category')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', 'newest')
    
    # Base queryset
    resources = Resource.objects.all()
    
    # Apply filters
    if status:
        resources = resources.filter(status=status)
    
    if resource_type:
        resources = resources.filter(resource_type__id=resource_type)
    
    if category:
        resources = resources.filter(category__id=category)
    
    if search_query:
        resources = resources.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(resource_type__name__icontains=search_query)
        )
    
    # Filter based on user type
    if hasattr(user, 'userprofile'):
        if user.userprofile.user_type == 'beneficiary':
            beneficiary = user.beneficiary_profile
            resources = resources.filter(
                Q(requested_by=beneficiary) | 
                Q(status='available')
            )
        elif user.userprofile.user_type == 'volunteer':
            volunteer = user.volunteer_profile
            resources = resources.filter(
                Q(offered_by=volunteer) | 
                Q(status='requested')
            )
    
    # Apply sorting
    if sort_by == 'newest':
        resources = resources.order_by('-created_at')
    elif sort_by == 'oldest':
        resources = resources.order_by('created_at')
    elif sort_by == 'name_asc':
        resources = resources.order_by('title')
    elif sort_by == 'name_desc':
        resources = resources.order_by('-title')
    
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
    
    return render(request, 'resources/resource_list.html', {
        'resources': page_obj,
        'resource_types': resource_types,
        'resource_categories': resource_categories,
        'selected_status': status,
        'selected_type': resource_type,
        'selected_category': category,
        'search_query': search_query,
        'sort_by': sort_by,
        'status_counts': status_dict
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
        if request.user.userprofile.user_type == 'beneficiary':
            has_feedback = match.feedbacks.filter(is_from_beneficiary=True).exists()
        elif request.user.userprofile.user_type == 'volunteer':
            has_feedback = match.feedbacks.filter(is_from_beneficiary=False).exists()
    
    # Get similar resources
    similar_resources = Resource.objects.filter(
        resource_type=resource.resource_type,
        status=resource.status
    ).exclude(id=resource.id)[:3]
    
    # Track resource view
    if not request.session.get(f'viewed_resource_{resource_id}'):
        resource.view_count += 1
        resource.save()
        request.session[f'viewed_resource_{resource_id}'] = True
    
    # Check if user can request/offer this resource
    can_request = False
    can_offer = False
    
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.user_type == 'beneficiary' and resource.status == 'available':
            can_request = True
        elif request.user.userprofile.user_type == 'volunteer' and resource.status == 'requested':
            can_offer = True
    
    return render(request, 'resources/resource_detail.html', {
        'resource': resource,
        'match': match,
        'has_feedback': has_feedback,
        'similar_resources': similar_resources,
        'can_request': can_request,
        'can_offer': can_offer
    })

@login_required
def request_resource(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'beneficiary':
        messages.error(request, 'Only beneficiaries can request resources.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        form = ResourceRequestForm(request.POST, request.FILES, beneficiary=request.user.beneficiary_profile)
        if form.is_valid():
            resource = form.save()
            
            # Create notification for admin
            create_notification(
                recipient=UserProfile.objects.filter(is_staff=True).first().user,
                title="New Resource Request",
                message=f"A new resource has been requested: {resource.title}",
                link=f"/resources/{resource.id}/"
            )
            
            messages.success(request, 'Resource request created successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceRequestForm(beneficiary=request.user.beneficiary_profile)
    
    return render(request, 'resources/request_resource.html', {
        'form': form,
        'resource_types': ResourceType.objects.all(),
        'resource_categories': ResourceCategory.objects.all()
    })

@login_required
def offer_resource(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'volunteer':
        messages.error(request, 'Only volunteers can offer resources.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        form = ResourceOfferForm(request.POST, request.FILES, volunteer=request.user.volunteer_profile)
        if form.is_valid():
            resource = form.save()
            
            # Create notification for admin
            create_notification(
                recipient=UserProfile.objects.filter(is_staff=True).first().user,
                title="New Resource Offer",
                message=f"A new resource has been offered: {resource.title}",
                link=f"/resources/{resource.id}/"
            )
            
            messages.success(request, 'Resource offer created successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceOfferForm(volunteer=request.user.volunteer_profile)
    
    return render(request, 'resources/offer_resource.html', {
        'form': form,
        'resource_types': ResourceType.objects.all(),
        'resource_categories': ResourceCategory.objects.all()
    })

@login_required
def edit_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user has permission to edit this resource
    if (hasattr(request.user, 'userprofile') and 
        request.user.userprofile.user_type == 'beneficiary' and 
        resource.requested_by != request.user.beneficiary_profile):
        messages.error(request, 'You do not have permission to edit this resource.')
        return redirect('resource_list')
    
    if (hasattr(request.user, 'userprofile') and 
        request.user.userprofile.user_type == 'volunteer' and 
        resource.offered_by != request.user.volunteer_profile):
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
    
    return render(request, 'resources/edit_resource.html', {
        'form': form, 
        'resource': resource,
        'resource_types': ResourceType.objects.all(),
        'resource_categories': ResourceCategory.objects.all()
    })

@login_required
def cancel_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user has permission to cancel this resource
    if (hasattr(request.user, 'userprofile') and 
        request.user.userprofile.user_type == 'beneficiary' and 
        resource.requested_by != request.user.beneficiary_profile):
        messages.error(request, 'You do not have permission to cancel this resource.')
        return redirect('resource_list')
    
    if (hasattr(request.user, 'userprofile') and 
        request.user.userprofile.user_type == 'volunteer' and 
        resource.offered_by != request.user.volunteer_profile):
        messages.error(request, 'You do not have permission to cancel this resource.')
        return redirect('resource_list')
    
    if request.method == 'POST':
        resource.status = 'cancelled'
        resource.updated_at = timezone.now()
        resource.save()
        
        # Create notification for admin
        create_notification(
            recipient=UserProfile.objects.filter(is_staff=True).first().user,
            title="Resource Cancelled",
            message=f"A resource has been cancelled: {resource.title}",
            link=f"/resources/{resource.id}/"
        )
        
        messages.success(request, 'Resource cancelled successfully.')
        return redirect('resource_list')
    
    return render(request, 'resources/cancel_resource.html', {'resource': resource})

@login_required
def resource_type_list(request):
    resource_types = ResourceType.objects.all().annotate(resource_count=Count('resources'))
    
    return render(request, 'resources/resource_type_list.html', {
        'resource_types': resource_types
    })

@login_required
def resource_type_detail(request, type_id):
    resource_type = get_object_or_404(ResourceType, id=type_id)
    resources = Resource.objects.filter(resource_type=resource_type)
    
    # Pagination
    paginator = Paginator(resources, 12)  # Show 12 resources per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'resources/resource_type_detail.html', {
        'resource_type': resource_type,
        'resources': page_obj
    })

@login_required
def resource_category_list(request):
    categories = ResourceCategory.objects.all().annotate(resource_count=Count('resources'))
    
    return render(request, 'resources/resource_category_list.html', {
        'categories': categories
    })

@login_required
def resource_category_detail(request, category_id):
    category = get_object_or_404(ResourceCategory, id=category_id)
    resources = Resource.objects.filter(category=category)
    
    # Pagination
    paginator = Paginator(resources, 12)  # Show 12 resources per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'resources/resource_category_detail.html', {
        'category': category,
        'resources': page_obj
    })

@login_required
def resource_map(request):
    # Get resources with location data
    resources = Resource.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    # Filter based on user type
    user = request.user
    if hasattr(user, 'userprofile'):
        if user.userprofile.user_type == 'beneficiary':
            beneficiary = user.beneficiary_profile
            resources = resources.filter(
                Q(requested_by=beneficiary) | 
                Q(status='available')
            )
        elif user.userprofile.user_type == 'volunteer':
            volunteer = user.volunteer_profile
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
    
    return render(request, 'resources/resource_map.html', {
        'resources': resources,
        'resource_types': resource_types,
        'resource_categories': resource_categories,
        'resource_data_json': resource_data
    })

@login_required
def beneficiary_categories(request):
    categories = ResourceCategory.objects.all()
    
    return render(request, 'resources/beneficiary_categories.html', {
        'categories': categories
    })

@login_required
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

