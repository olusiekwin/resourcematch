from django import forms
from .models import SMSPreference

class SMSPreferenceForm(forms.ModelForm):
    class Meta:
        model = SMSPreference
        fields = [
            'receive_match_notifications',
            'receive_resource_updates',
            'receive_campaign_updates',
            'receive_feedback_notifications',
            'receive_general_notifications'
        ]
        widgets = {
            'receive_match_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receive_resource_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receive_campaign_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receive_feedback_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receive_general_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

