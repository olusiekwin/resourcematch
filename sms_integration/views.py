from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from twilio.twiml.messaging_response import MessagingResponse
from .models import SMSPreference
from .forms import SMSPreferenceForm

@login_required
def sms_preferences(request):
    """View for managing SMS preferences"""
    try:
        preference = SMSPreference.objects.get(user=request.user)
    except SMSPreference.DoesNotExist:
        preference = SMSPreference.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = SMSPreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            messages.success(request, 'SMS preferences updated successfully.')
            return redirect('sms_preferences')
    else:
        form = SMSPreferenceForm(instance=preference)
    
    return render(request, 'sms_integration/sms_preferences.html', {
        'form': form
    })

@csrf_exempt
@require_POST
def twilio_webhook(request):
    """Webhook for Twilio SMS responses"""
    # Get the message content and sender
    message_body = request.POST.get('Body', '')
    from_number = request.POST.get('From', '')
    
    # Create a response
    resp = MessagingResponse()
    
    # Simple auto-responder
    if message_body.lower().startswith('help'):
        resp.message("Welcome to ResourceMatch! Reply with:\n"
                    "INFO - Get information about our services\n"
                    "STOP - Unsubscribe from SMS notifications")
    elif message_body.lower().startswith('info'):
        resp.message("ResourceMatch connects beneficiaries with volunteers and resources. "
                    "Visit our website at www.resourcematch.org for more information.")
    elif message_body.lower().startswith('stop'):
        # Handle unsubscribe request
        resp.message("You have been unsubscribed from ResourceMatch SMS notifications. "
                    "Reply with START to resubscribe.")
    else:
        resp.message("Thank you for your message. For assistance, please reply with HELP.")
    
    return HttpResponse(str(resp), content_type='text/xml')

