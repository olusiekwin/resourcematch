from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings

from .models import Resource, ResourceType, ResourceCategory
from .forms import ResourceForm, ResourceRequestForm, ResourceOfferForm, ResourceTypeForm
from notifications.utils import create_notification
from sms.utils import send_sms

@login_required
def resource_list(request):
    user = request.user
    
    # Get filter parameters
    status = request.GET.get('status')
    resource_type = request.GET.get('type')
    category = request.GET.get('category')
    search_query = request.GET.get('q')
    
    # Base queryset
    resources = Resource.objects.all().select_related(
        'resource_type', 'requested_by', 'offered_by'
    ).order_by('-created_at')
    
    # Apply filters
    if status:
        resources = resources.filter(status=status)
    
    if resource_type:
        resources = resources.filter(resource_type__id=resource_type)
    
    if category:
        resources = resources.filter(resource_type__category__id=category)
    
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
    
    # Get all resource types and categories for filter dropdown
    resource_types = ResourceType.objects.all()
    categories = ResourceCategory.objects.all()
    
    # Add counts for each status
    status_counts = {
        'all': resources.count(),
        'available': resources.filter(status='available').count(),
        'requested': resources.filter(status='requested').count(),
        'matched': resources.filter(status='matched').count(),
        'completed': resources.filter(status='completed').count(),
        'cancelled': resources.filter(status='cancelled').count(),
    }
    
    # Pagination
    paginator = Paginator(resources, 12)  # Show 12 resources per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'resources/resource_list.html', {
        'resources': page_obj,
        'resource_types': resource_types,
        'categories': categories,
        'selected_status': status,
        'selected_type': resource_type,
        'selected_category': category,
        'search_query': search_query,
        'status_counts': status_counts,
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
        'can_offer': can_offer,
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
                recipient=None,  # Admin notification
                sender=request.user,
                notification_type='resource_requested',
                title='New Resource Request',
                message=f'A new resource has been requested: {resource.title}',
                related_object=resource
            )
            
            # Send SMS notification to admin
            admin_phone = '+1234567890'  # Replace with actual admin phone
            sms_message = f'New resource request: {resource.title} by {request.user.get_full_name()}'
            send_sms(admin_phone, sms_message)
            
            messages.success(request, 'Resource request created successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        # Pre-fill form if coming from an available resource
        resource_id = request.GET.get('resource_id')
        if resource_id:
            try:
                available_resource = Resource.objects.get(id=resource_id, status='available')
                form = ResourceRequestForm(
                    beneficiary=request.user.beneficiary_profile,
                    initial={
                        'resource_type': available_resource.resource_type,
                        'title': f"Request for {available_resource.title}",
                        'description': f"I would like to request this resource: {available_resource.description}",
                    }
                )
            except Resource.DoesNotExist:
                form = ResourceRequestForm(beneficiary=request.user.beneficiary_profile)
        else:
            form = ResourceRequestForm(beneficiary=request.user.beneficiary_profile)
    
    # Get resource types for the form
    resource_types = ResourceType.objects.all()
    
    return render(request, 'resources/request_resource.html', {
        'form': form,
        'resource_types': resource_types
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
                recipient=None,  # Admin notification
                sender=request.user,
                notification_type='resource_offered',
                title='New Resource Offer',
                message=f'A new resource has been offered: {resource.title}',
                related_object=resource
            )
            
            # Send SMS notification to admin
            admin_phone = '+1234567890'  # Replace with actual admin phone
            sms_message = f'New resource offer: {resource.title} by {request.user.get_full_name()}'
            send_sms(admin_phone, sms_message)
            
            messages.success(request, 'Resource offer created successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        # Pre-fill form if coming from a requested resource
        resource_id = request.GET.get('resource_id')
        if resource_id:
            try:
                requested_resource = Resource.objects.get(id=resource_id, status='requested')
                form = ResourceOfferForm(
                    volunteer=request.user.volunteer_profile,
                    initial={
                        'resource_type': requested_resource.resource_type,
                        'title': f"Offer for {requested_resource.title}",
                        'description': f"I would like to offer this resource: {requested_resource.description}",
                    }
                )
            except Resource.DoesNotExist:
                form = ResourceOfferForm(volunteer=request.user.volunteer_profile)
        else:
            form = ResourceOfferForm(volunteer=request.user.volunteer_profile)
    
    # Get resource types for the form
    resource_types = ResourceType.objects.all()
    
    return render(request, 'resources/offer_resource.html', {
        'form': form,
        'resource_types': resource_types
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
    
    # Only allow editing if resource is not matched or completed
    if resource.status in ['matched', 'completed']:
        messages.error(request, 'You cannot edit a resource that is already matched or completed.')
        return redirect('resource_detail', resource_id=resource.id)
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resource updated successfully.')
            return redirect('resource_detail', resource_id=resource.id)
    else:
        form = ResourceForm(instance=resource)
    
    return render(request, 'resources/edit_resource.html', {
        'form': form,
        'resource': resource
    })

@login_required
@require_POST
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
    
    # Only allow cancellation if resource is not matched or completed
    if resource.status in ['matched', 'completed']:
        messages.error(request, 'You cannot cancel a resource that is already matched or completed.')
        return redirect('resource_detail', resource_id=resource.id)
    
    resource.status = 'cancelled'
    resource.cancelled_at = timezone.now()
    resource.save()
    
    # Create notification for admin
    create_notification(
        recipient=None,  # Admin notification
        sender=request.user,
        notification_type='resource_cancelled',
        title='Resource Cancelled',
        message=f'A resource has been cancelled: {resource.title}',
        related_object=resource
    )
    
    messages.success(request, 'Resource cancelled successfully.')
    return redirect('resource_list')

@login_required
def resource_type_list(request):
    resource_types = ResourceType.objects.all().annotate(
        resource_count=Count('resources')
    )
    
    # Group by category
    categories = ResourceCategory.objects.all().prefetch_related('resource_types')
    
    return render(request, 'resources/resource_type_list.html', {
        'resource_types': resource_types,
        'categories': categories
    })

@login_required
def resource_type_detail(request, type_id):
    resource_type = get_object_or_404(ResourceType, id=type_id)
    
    # Get resources of this type
    resources = Resource.objects.filter(resource_type=resource_type).order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        resources = resources.filter(status=status)
    
    # Pagination
    paginator = Paginator(resources, 12)  # Show 12 resources per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Status counts
    status_counts = {
        'all': resources.count(),
        'available': resources.filter(status='available').count(),
        'requested': resources.filter(status='requested').count(),
        'matched': resources.filter(status='matched').count(),
        'completed': resources.filter(status='completed').count(),
        'cancelled': resources.filter(status='cancelled').count(),
    }
    
    return render(request, 'resources/resource_type_detail.html', {
        'resource_type': resource_type,
        'resources': page_obj,
        'selected_status': status,
        'status_counts': status_counts
    })

@login_required
def resource_category_list(request):
    categories = ResourceCategory.objects.all().prefetch_related('resource_types')
    
    return render(request, 'resources/resource_category_list.html', {
        'categories': categories
    })

@login_required
def resource_category_detail(request, category_id):
    category = get_object_or_404(ResourceCategory, id=category_id)
    
    # Get resource types in this category
    resource_types = ResourceType.objects.filter(category=category).annotate(
        resource_count=Count('resources')
    )
    
    # Get resources in this category
    resources = Resource.objects.filter(resource_type__category=category).order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        resources = resources.filter(status=status)
    
    # Pagination
    paginator = Paginator(resources, 12)  # Show 12 resources per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Status counts
    status_counts = {
        'all': resources.count(),
        'available': resources.filter(status='available').count(),
        'requested': resources.filter(status='requested').count(),
        'matched': resources.filter(status='matched').count(),
        'completed': resources.filter(status='completed').count(),
        'cancelled': resources.filter(status='cancelled').count(),
    }
    
    return render(request, 'resources/resource_category_detail.html', {
        'category': category,
        'resource_types': resource_types,
        'resources': page_obj,
        'selected_status': status,
        'status_counts': status_counts
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
    
    # Filter by type if provided
    resource_type = request.GET.get('type')
    if resource_type:
        resources = resources.filter(resource_type__id=resource_type)
    
    # Filter by category if provided
    category = request.GET.get('category')
    if category:
        resources = resources.filter(resource_type__category__id=category)
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        resources = resources.filter(status=status)
    
    # Get all resource types and categories for filter
    resource_types = ResourceType.objects.all()
    categories = ResourceCategory.objects.all()
    
    # Prepare resource data for the map
    resource_data = []
    for resource in resources:
        resource_data.append({
            'id': resource.id,
            'title': resource.title,
            'type': resource.resource_type.name,
            'category': resource.resource_type.category.name if resource.resource_type.category else 'Uncategorized',
            'status': resource.get_status_display(),
            'latitude': float(resource.latitude),
            'longitude': float(resource.longitude),
            'url': f'/resources/{resource.id}/',
            'icon': resource.resource_type.icon_class if resource.resource_type.icon_class else 'bi-box',
            'color': resource.get_status_color(),
        })
    
    return render(request, 'resources/resource_map.html', {
        'resources': resources,
        'resource_types': resource_types,
        'categories': categories,
        'selected_type': resource_type,
        'selected_category': category,
        'selected_status': status,
        'resource_data_json': resource_data,
        'map_api_key': settings.MAP_API_KEY,
    })

@login_required
def beneficiary_categories(request):
    categories = ResourceCategory.objects.all().prefetch_related('resource_types')
    
    return render(request, 'resources/beneficiary_categories.html', {
        'categories': categories
    })

@login_required
@require_POST
def resource_action(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    action = request.POST.get('action')
    
    if action == 'request':
        # Check if user is a beneficiary
        if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'beneficiary':
            return JsonResponse({'status': 'error', 'message': 'Only beneficiaries can request resources.'})
        
        # Check if resource is available
        if resource.status != 'available':
            return JsonResponse({'status': 'error', 'message': 'This resource is not available for request.'})
        
        # Create a new resource request based on this available resource
        new_resource = Resource.objects.create(
            resource_type=resource.resource_type,
            title=f"Request for {resource.title}",
            description=f"I would like to request this resource: {resource.description}",
            requested_by=request.user.beneficiary_profile,
            status='requested',
            latitude=resource.latitude,
            longitude=resource.longitude,
        )
        
        # Create notification for the volunteer who offered the resource
        if resource.offered_by:
            create_notification(
                recipient=resource.offered_by.user,
                sender=request.user,
                notification_type='resource_requested',
                title='Resource Requested',
                message=f'Your offered resource "{resource.title}" has been requested.',
                related_object=new_resource
            )
            
            # Send SMS notification
            if resource.offered_by.phone:
                sms_message = f'Your offered resource "{resource.title}" has been requested by {request.user.get_full_name()}.'
                send_sms(resource.offered_by.phone, sms_message)
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Resource requested successfully.',
            'redirect_url': f'/resources/{new_resource.id}/'
        })
    
    elif action == 'offer':
        # Check if user is a volunteer
        if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'volunteer':
            return JsonResponse({'status': 'error', 'message': 'Only volunteers can offer resources.'})
        
        # Check if resource is requested
        if resource.status != 'requested':
            return JsonResponse({'status': 'error', 'message': 'This resource is not available for offering.'})
        
        # Create a new resource offer based on this requested resource
        new_resource = Resource.objects.create(
            resource_type=resource.resource_type,
            title=f"Offer for {resource.title}",
            description=f"I would like to offer this resource: {resource.description}",
            offered_by=request.user.volunteer_profile,
            status='available',
            latitude=resource.latitude,
            longitude=resource.longitude,
        )
        
        # Create notification for the beneficiary who requested the resource
        if resource.requested_by:
            create_notification(
                recipient=resource.requested_by.user,
                sender=request.user,
                notification_type='resource_offered',
                title='Resource Offered',
                message=f'Your requested resource "{resource.title}" has been offered.',
                related_object=new_resource
            )
            
            # Send SMS notification
            if resource.requested_by.phone:
                sms_message = f'Your requested resource "{resource.title}" has been offered by {request.user.get_full_name()}.'
                send_sms(resource.requested_by.phone, sms_message)
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Resource offered successfully.',
            'redirect_url': f'/resources/{new_resource.id}/'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid action.'})

@login_required
def search_resources(request):
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'results': []})
    
    resources = Resource.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(resource_type__name__icontains=query)
    )[:10]
    
    results = []
    for resource in resources:
        results.append({
            'id': resource.id,
            'title': resource.title,
            'type': resource.resource_type.name,
            'status': resource.get_status_display(),
            'url': f'/resources/{resource.id}/'
        })
    
    return JsonResponse({'results': results})

