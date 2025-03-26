from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .models import SmsLog, SmsTemplate
from .utils import send_sms, send_template_sms, bulk_send_sms
from .serializers import SmsLogSerializer, SmsTemplateSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_sms_api(request):
    """API endpoint for sending SMS"""
    recipient = request.data.get('recipient')
    message = request.data.get('message')
    
    if not recipient or not message:
        return Response(
            {'error': 'Recipient and message are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    response = send_sms(recipient, message)
    
    if response['success']:
        return Response(response, status=status.HTTP_200_OK)
    else:
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_template_sms_api(request):
    """API endpoint for sending template SMS"""
    recipient = request.data.get('recipient')
    template_key = request.data.get('template_key')
    context = request.data.get('context', {})
    
    if not recipient or not template_key:
        return Response(
            {'error': 'Recipient and template_key are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    response = send_template_sms(recipient, template_key, context)
    
    if response['success']:
        return Response(response, status=status.HTTP_200_OK)
    else:
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def sms_logs_api(request):
    """API endpoint for retrieving SMS logs"""
    logs = SmsLog.objects.all()
    
    # Filter by status if provided
    status_filter = request.query_params.get('status')
    if status_filter:
        logs = logs.filter(status=status_filter)
    
    # Filter by date range if provided
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    if start_date and end_date:
        logs = logs.filter(sent_at__range=[start_date, end_date])
    
    # Filter by recipient if provided
    recipient = request.query_params.get('recipient')
    if recipient:
        logs = logs.filter(recipient__icontains=recipient)
    
    # Pagination
    page = self.paginate_queryset(logs)
    if page is not None:
        serializer = SmsLogSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    serializer = SmsLogSerializer(logs, many=True)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def sms_templates_api(request):
    """API endpoint for managing SMS templates"""
    if request.method == 'GET':
        templates = SmsTemplate.objects.all()
        serializer = SmsTemplateSerializer(templates, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = SmsTemplateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

