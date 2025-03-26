import logging
from django.conf import settings
import africastalking
from .models import SMSLog, SMSTemplate

logger = logging.getLogger(__name__)

def get_africastalking_client():
    """Get Africa's Talking client using settings"""
    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    
    if not username or not api_key:
        logger.error("Africa's Talking credentials not configured")
        return None
    
    # Initialize Africa's Talking
    africastalking.initialize(username, api_key)
    return africastalking.SMS

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
    
    # Get Africa's Talking client
    sms_service = get_africastalking_client()
    if not sms_service:
        sms_log.status = 'failed'
        sms_log.error_message = "Africa's Talking client not configured"
        sms_log.save()
        return sms_log
    
    # Send SMS via Africa's Talking
    try:
        response = sms_service.send(
            message=message,
            recipients=[phone_number],
            sender_id=settings.AFRICASTALKING_SENDER_ID
        )
        
        # Process response
        if response and 'SMSMessageData' in response and 'Recipients' in response['SMSMessageData']:
            recipients = response['SMSMessageData']['Recipients']
            if recipients and len(recipients) > 0:
                recipient_status = recipients[0]
                
                # Update SMS log
                sms_log.status = 'sent' if recipient_status.get('status') == 'Success' else 'failed'
                sms_log.external_id = recipient_status.get('messageId')
                
                if recipient_status.get('status') != 'Success':
                    sms_log.error_message = recipient_status.get('statusReason')
                
                sms_log.save()
                
                logger.info(f"SMS sent to {phone_number}: {message[:50]}...")
        else:
            # Handle unexpected response format
            sms_log.status = 'failed'
            sms_log.error_message = "Unexpected response format from Africa's Talking"
            sms_log.save()
            
            logger.error(f"Failed to send SMS: Unexpected response format")
        
    except Exception as e:
        # Handle Africa's Talking errors
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
    if match.beneficiary and match.beneficiary.user.userprofile and hasattr(match.beneficiary.user, 'sms_preference') and match.beneficiary.user.sms_preference.receive_match_notifications:
        beneficiary = match.beneficiary
        message = render_sms_template('match_notification_beneficiary', {
            'beneficiary_name': beneficiary.user.get_full_name() or beneficiary.user.username,
            'resource_title': match.resource.title,
            'volunteer_name': match.volunteer.user.get_full_name() or match.volunteer.user.username
        })
        
        if message:
            send_sms(beneficiary.user.userprofile, message, 'match_notification_beneficiary')
    
    # Notify volunteer
    if match.volunteer and match.volunteer.user.userprofile and hasattr(match.volunteer.user, 'sms_preference') and match.volunteer.user.sms_preference.receive_match_notifications:
        volunteer = match.volunteer
        message = render_sms_template('match_notification_volunteer', {
            'volunteer_name': volunteer.user.get_full_name() or volunteer.user.username,
            'resource_title': match.resource.title,
            'beneficiary_name': match.beneficiary.user.get_full_name() or match.beneficiary.user.username
        })
        
        if message:
            send_sms(volunteer.user.userprofile, message, 'match_notification_volunteer')

