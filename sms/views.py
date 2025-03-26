from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import SmsLog, SmsTemplate
from .utils import send_sms, send_template_sms, bulk_send_sms
from .forms import SmsForm, BulkSmsForm, SmsTemplateForm

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def sms_dashboard(request):
    """Dashboard for SMS management"""
    # Get recent SMS logs
    recent_logs = SmsLog.objects.all()[:20]
    
    # Get SMS templates
    templates = SmsTemplate.objects.all()
    
    # SMS stats
    total_sent = SmsLog.objects.count()
    successful = SmsLog.objects.filter(status='Success').count()
    failed = total_sent - successful
    
    # SMS form
    sms_form = SmsForm()
    bulk_sms_form = BulkSmsForm()
    
    context = {
        'recent_logs': recent_logs,
        'templates': templates,
        'total_sent': total_sent,
        'successful': successful,
        'failed': failed,
        'sms_form': sms_form,
        'bulk_sms_form': bulk_sms_form,
    }
    
    return render(request, 'sms/dashboard.html', context)

@login_required
@user_passes_test(is_staff)
def sms_logs(request):
    """View all SMS logs with filtering"""
    logs = SmsLog.objects.all()
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        logs = logs.filter(status=status)
    
    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        logs = logs.filter(sent_at__range=[start_date, end_date])
    
    # Filter by recipient if provided
    recipient = request.GET.get('recipient')
    if recipient:
        logs = logs.filter(recipient__icontains=recipient)
    
    context = {
        'logs': logs,
        'status_filter': status,
        'start_date': start_date,
        'end_date': end_date,
        'recipient': recipient,
    }
    
    return render(request, 'sms/logs.html', context)

@login_required
@user_passes_test(is_staff)
def sms_templates(request):
    """View and manage SMS templates"""
    templates = SmsTemplate.objects.all()
    
    if request.method == 'POST':
        form = SmsTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'SMS template created successfully.')
            return redirect('sms_templates')
    else:
        form = SmsTemplateForm()
    
    context = {
        'templates': templates,
        'form': form,
    }
    
    return render(request, 'sms/templates.html', context)

@login_required
@user_passes_test(is_staff)
def edit_template(request, template_id):
    """Edit an SMS template"""
    template = get_object_or_404(SmsTemplate, id=template_id)
    
    if request.method == 'POST':
        form = SmsTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'SMS template updated successfully.')
            return redirect('sms_templates')
    else:
        form = SmsTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
    }
    
    return render(request, 'sms/edit_template.html', context)

@login_required
@user_passes_test(is_staff)
@require_POST
def delete_template(request, template_id):
    """Delete an SMS template"""
    template = get_object_or_404(SmsTemplate, id=template_id)
    template.delete()
    messages.success(request, 'SMS template deleted successfully.')
    return redirect('sms_templates')

@login_required
@user_passes_test(is_staff)
@require_POST
def send_single_sms(request):
    """Send a single SMS"""
    form = SmsForm(request.POST)
    if form.is_valid():
        recipient = form.cleaned_data['recipient']
        message = form.cleaned_data['message']
        
        response = send_sms(recipient, message)
        
        if response['success']:
            messages.success(request, f'SMS sent successfully to {recipient}.')
        else:
            messages.error(request, f'Failed to send SMS: {response["error"]}')
        
        return redirect('sms_dashboard')
    
    messages.error(request, 'Invalid form data.')
    return redirect('sms_dashboard')

@login_required
@user_passes_test(is_staff)
@require_POST
def send_bulk_sms(request):
    """Send SMS to multiple recipients"""
    form = BulkSmsForm(request.POST)
    if form.is_valid():
        recipients = form.cleaned_data['recipients'].split(',')
        recipients = [r.strip() for r in recipients]
        message = form.cleaned_data['message']
        
        response = bulk_send_sms(recipients, message)
        
        if response['success']:
            messages.success(request, f'SMS sent successfully to {len(recipients)} recipients.')
        else:
            messages.error(request, f'Failed to send SMS: {response["error"]}')
        
        return redirect('sms_dashboard')
    
    messages.error(request, 'Invalid form data.')
    return redirect('sms_dashboard')

@login_required
@user_passes_test(is_staff)
@require_POST
def send_template(request):
    """Send SMS using a template"""
    template_id = request.POST.get('template_id')
    recipient = request.POST.get('recipient')
    
    if not template_id or not recipient:
        messages.error(request, 'Template ID and recipient are required.')
        return redirect('sms_dashboard')
    
    template = get_object_or_404(SmsTemplate, id=template_id)
    
    # Get context variables from POST data
    context = {}
    for key, value in request.POST.items():
        if key.startswith('var_'):
            var_name = key[4:]  # Remove 'var_' prefix
            context[var_name] = value
    
    response = send_template_sms(recipient, template.template_key, context)
    
    if response['success']:
        messages.success(request, f'Template SMS sent successfully to {recipient}.')
    else:
        messages.error(request, f'Failed to send template SMS: {response["error"]}')
    
    return redirect('sms_dashboard')

@csrf_exempt
def africas_talking_callback(request):
    """Callback endpoint for Africa's Talking"""
    if request.method == 'POST':
        # Process the callback data
        data = request.POST
        
        # Update the SMS log if message ID exists
        message_id = data.get('id')
        if message_id:
            try:
                sms_log = SmsLog.objects.get(message_id=message_id)
                sms_log.status = data.get('status', 'Unknown')
                sms_log.save()
            except SmsLog.DoesNotExist:
                pass
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'})

