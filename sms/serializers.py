from rest_framework import serializers
from .models import SmsLog, SmsTemplate

class SmsLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsLog
        fields = '__all__'

class SmsTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsTemplate
        fields = '__all__'

