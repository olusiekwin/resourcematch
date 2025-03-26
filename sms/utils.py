import africastalking
from django.conf import settings
from .models import SmsLog, SmsTemplate

def initialize_africastalking():
    """Initialize the Africa's Talking SDK"""
    username = settings.AFRICAS_TALKING_USERNAME
    api_key = settings.AFRICAS_TALKING_API_KEY
    
    # Initialize the SDK
    africastalking.initialize(username, api_key)
    
    # Get the SMS service
    sms = africastalking.SMS
    
    return sms

def send_sms(recipient, message, sender_id=None):
    """
    Send SMS using Africa's Talking API
    
    Args:
        recipient (str): Phone number in international format (e.g., +254711XXXYYY)
        message (str): SMS content
        sender_id (str, optional): Sender ID. Defaults to settings.AFRICAS_TALKING_SENDER_ID.
    
    Returns:
        dict: Response from Africa's Talking API
    """
    try:
        # Initialize Africa's Talking
        sms = initialize_africastalking()
        
        # Set sender ID
        if not sender_id:
            sender_id = settings.AFRICAS_TALKING_SENDER_ID
        
        # Send the message
        response = sms.send(message, [recipient], sender_id)
        
        # Log the SMS
        status = response['SMSMessageData']['Recipients'][0]['status']
        message_id = response['SMSMessageData']['Recipients'][0].get('messageId', '')
        cost = float(response['SMSMessageData']['Recipients'][0].get('cost', '0').replace('KES ', ''))
        
        SmsLog.objects.create(
            recipient=recipient,
            message=message,
            status=status,
            message_id=message_id,
            cost=cost
        )
        
        return {
            'success': True,
            'status': status,
            'message_id': message_id,
            'cost': cost
        }
    
    except Exception as e:
        # Log the error
        SmsLog.objects.create(
            recipient=recipient,
            message=message,
            status=f"Error: {str(e)}"
        )
        
        return {
            'success': False,
            'error': str(e)
        }

def send_template_sms(recipient, template_key, context=None, sender_id=None):
    """
    Send SMS using a predefined template
    
    Args:
        recipient (str): Phone number in international format
        template_key (str): Template key/slug
        context (dict, optional): Variables to replace in the template. Defaults to None.
        sender_id (str, optional): Sender ID. Defaults to None.
    
    Returns:
        dict: Response from send_sms function
    """
    try:
        # Get the template
        template = SmsTemplate.objects.get(template_key=template_key)
        
        # Replace variables in the template
        message = template.content
        if context:
            for key, value in context.items():
                message = message.replace(f"{{{key}}}", str(value))
        
        # Send the SMS
        return send_sms(recipient, message, sender_id)
    
    except SmsTemplate.DoesNotExist:
        return {
            'success': False,
            'error': f"Template with key '{template_key}' does not exist"
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def bulk_send_sms(recipients, message, sender_id=None):
    """
    Send the same SMS to multiple recipients
    
    Args:
        recipients (list): List of phone numbers
        message (str): SMS content
        sender_id (str, optional): Sender ID. Defaults to None.
    
    Returns:
        dict: Response from Africa's Talking API
    """
    try:
        # Initialize Africa's Talking
        sms = initialize_africastalking()
        
        # Set sender ID
        if not sender_id:
            sender_id = settings.AFRICAS_TALKING_SENDER_ID
        
        # Send the message
        response = sms.send(message, recipients, sender_id)
        
        # Log each SMS
        results = []
        for recipient_data in response['SMSMessageData']['Recipients']:
            recipient = recipient_data['number']
            status = recipient_data['status']
            message_id = recipient_data.get('messageId', '')
            cost = float(recipient_data.get('cost', '0').replace('KES ', ''))
            
            SmsLog.objects.create(
                recipient=recipient,
                message=message,
                status=status,
                message_id=message_id,
                cost=cost
            )
            
            results.append({
                'recipient': recipient,
                'status': status,
                'message_id': message_id,
                'cost': cost
            })
        
        return {
            'success': True,
            'results': results
        }
    
    except Exception as e:
        # Log the error for each recipient
        for recipient in recipients:
            SmsLog.objects.create(
                recipient=recipient,
                message=message,
                status=f"Error: {str(e)}"
            )
        
        return {
            'success': False,
            'error': str(e)
        }

