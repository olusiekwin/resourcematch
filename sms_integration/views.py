from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import SMSPreference, SMSLog
from .forms import SMSPreferenceForm
import json

@login_required
def sms_preferences(request):
    """View for managing SMS preferences"""
    try:
        preference = SMSPreference.objects.get(user=request.user)
    except SMSPreference.DoesNotExist:
        preference = SMSPreference.objects.create(user=request.user)
    
    # Get user's SMS logs
    sms_logs = SMSLog.objects.filter(recipient=request.user.userprofile).order_by('-sent_at')[:10]
    
    if request.method == 'POST':
        form = SMSPreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            messages.success(request, 'SMS preferences updated successfully.')
            return redirect('sms_preferences')
    else:
        form = SMSPreferenceForm(instance=preference)
    
    return render(request, 'sms_integration/sms_preferences.html', {
        'form': form,
        'sms_logs': sms_logs
    })

@csrf_exempt
def africastalking_callback(request):
    """Callback URL for Africa's Talking delivery reports"""
    if request.method == 'POST':
        try:
            # Parse the JSON data from Africa's Talking
            data = json.loads(request.body)
            
            # Extract information from the callback
            message_id = data.get('id')
            status = data.get('status')
            
            if message_id and status:
                # Update the SMS log with the delivery status
                sms_logs = SMSLog.objects.filter(external_id=message_id)
                if sms_logs.exists():
                    sms_log = sms_logs.first()
                    
                    # Map Africa's Talking status to our status
                    if status.lower() == 'success':
                        sms_log.status = 'delivered'
                        sms_log.save()
                    elif status.lower() in ['failed', 'rejected']:
                        sms_log.status = 'failed'
                        sms_log.error_message = data.get('failureReason', 'Delivery failed')
                        sms_log.save()
            
            return HttpResponse(status=200)
        
        except Exception as e:
            return HttpResponse(f"Error processing callback: {str(e)}", status=400)
    
    return HttpResponse("Method not allowed", status=405)

@csrf_exempt
@require_POST
def incoming_sms(request):
    """Handler for incoming SMS messages"""
    # Extract SMS data from the request
    from_number = request.POST.get('from')
    to_number = request.POST.get('to')
    message = request.POST.get('text', '')
    
    # Simple auto-responder logic
    response = {
        'message': '',
    }
    
    if message.lower().startswith('help'):
        response['message'] = ("Welcome to ResourceMatch! Reply with:\n"
                         "INFO - Get information about our services\n"
                         "STOP - Unsubscribe from SMS notifications")
    elif message.lower().startswith('info'):
        response['message'] = ("ResourceMatch connects beneficiaries with volunteers and resources. "
                         "Visit our website for more information.")
    elif message.lower().startswith('stop'):
        # Handle unsubscribe request
        response['message'] = ("You have been unsubscribed from ResourceMatch SMS notifications. "
                         "Reply with START to resubscribe.")
        
        # Find user with this phone number and update their preferences
        if from_number:
            from_number = from_number.strip()
            if from_number.startswith('+'):
                # Try to find users with this phone number
                from accounts.models import UserProfile
                user_profiles = UserProfile.objects.filter(phone_number__endswith=from_number[-9:])
                
                for profile in user_profiles:
                    if hasattr(profile.user, 'sms_preference'):
                        # Unsubscribe from all notifications
                        sms_pref = profile.user.sms_preference
                        sms_pref.receive_match_notifications = False
                        sms_pref.receive_resource_updates = False
                        sms_pref.receive_campaign_updates = False
                        sms_pref.receive_feedback_notifications = False
                        sms_pref.receive_general_notifications = False
                        sms_pref.save()
    elif message.lower().startswith('start'):
        response['message'] = ("You have been resubscribed to ResourceMatch SMS notifications. "
                         "Reply with HELP for more information.")
        
        # Find user with this phone number and update their preferences
        if from_number:
            from_number = from_number.strip()
            if from_number.startswith('+'):
                # Try to find users with this phone number
                from accounts.models import UserProfile
                user_profiles = UserProfile.objects.filter(phone_number__endswith=from_number[-9:])
                
                for profile in user_profiles:
                    if hasattr(profile.user, 'sms_preference'):
                        # Resubscribe to all notifications
                        sms_pref = profile.user.sms_preference
                        sms_pref.receive_match_notifications = True
                        sms_pref.receive_resource_updates = True
                        sms_pref.receive_campaign_updates = True
                        sms_pref.receive_feedback_notifications = True
                        sms_pref.receive_general_notifications = True
                        sms_pref.save()
    else:
        response['message'] = "Thank you for your message. For assistance, please reply with HELP."
    
    return JsonResponse(response)

