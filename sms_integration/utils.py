import logging
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from .models import SMSLog, SMSTemplate

logger = logging.getLogger(__name__)

def get_twilio_client():
    """Get Twilio client using settings"""
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    
    if not account_sid or not auth_token:
        logger.error("Twilio credentials not configured")
        return None
    
    return Client(account_sid, auth_token)

def send_sms(recipient, message, template=None):
    """
    Send SMS to a user
    
    Args:
        recipient: UserProfile instance
        message: SMS message text
        template: SMSTemplate instance or template name
    
    Returns:
        SMSLog instance
    """
    # Check if user has a phone number
    if not recipient.phone_number:
        logger.error(f"No phone number for user {recipient.user.username}")
        return None
    
    # Format phone number (ensure it has country code)
    phone_number = recipient.phone_number
    if not phone_number.startswith('+'):
        phone_number = f"+{phone_number}"
    
    # Get template if name is provided
    if template and isinstance(template, str):
        try:
            template = SMSTemplate.objects.get(name=template)
        except SMSTemplate.DoesNotExist:
            template = None
    
    # Create SMS log entry
    sms_log = SMSLog.objects.create(
        recipient=recipient,
        phone_number=phone_number,
        message=message,
        template=template,
        status='pending'
    )
    
    # Get Twilio client
    client = get_twilio_client()
    if not client:
        sms_log.status = 'failed'
        sms_log.error_message = "Twilio client not configured"
        sms_log.save()
        return sms_log
    
    # Send SMS via Twilio
    try:
        twilio_message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        # Update SMS log
        sms_log.status = 'sent'
        sms_log.external_id = twilio_message.sid
        sms_log.save()
        
        logger.info(f"SMS sent to {phone_number}: {message[:50]}...")
        
    except TwilioRestException as e:
        # Handle Twilio errors
        sms_log.status = 'failed'
        sms_log.error_message = str(e)
        sms_log.save()
        
        logger.error(f"Failed to send SMS: {str(e)}")
    
    return sms_log

def render_sms_template(template_name, context=None):
    """
    Render SMS template with context
    
    Args:
        template_name: Name of the template
        context: Dictionary of variables to replace in template
    
    Returns:
        Rendered message text
    """
    if context is None:
        context = {}
    
    try:
        template = SMSTemplate.objects.get(name=template_name)
        message = template.template_text
        
        # Replace variables in template
        for key, value in context.items():
            placeholder = '{' + key + '}'
            message = message.replace(placeholder, str(value))
        
        return message
    
    except SMSTemplate.DoesNotExist:
        logger.error(f"SMS template not found: {template_name}")
        return None

def send_match_notification_sms(match):
    """Send SMS notification for a new match"""
    # Notify beneficiary
    if match.resource.requested_by and match.resource.requested_by.user.sms_preference.receive_match_notifications:
        beneficiary = match.resource.requested_by
        message = render_sms_template('match_notification_beneficiary', {
            'beneficiary_name': beneficiary.user.get_full_name() or beneficiary.user.username,
            'resource_title': match.resource.title,
            'volunteer_name': match.volunteer.user.get_full_name() or match.volunteer.user.username
        })
        
        if message:
            send_sms(beneficiary.user.userprofile, message, 'match_notification_beneficiary')
    
    # Notify volunteer
    if match.volunteer and match.volunteer.user.sms_preference.receive_match_notifications:
        volunteer = match.volunteer
        message = render_sms_template('match_notification_volunteer', {
            'volunteer_name': volunteer.user.get_full_name() or volunteer.user.username,
            'resource_title': match.resource.title,
            'beneficiary_name': match.resource.requested_by.user.get_full_name() or match.resource.requested_by.user.username
        })
        
        if message:
            send_sms(volunteer.user.userprofile, message, 'match_notification_volunteer')

