from django import forms
from .models import SmsTemplate

class SmsForm(forms.Form):
    """Form for sending a single SMS"""
    recipient = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254711XXXYYY'}),
        help_text='Phone number in international format (e.g., +254711XXXYYY)'
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        help_text='SMS content (160 characters per SMS)'
    )

class BulkSmsForm(forms.Form):
    """Form for sending SMS to multiple recipients"""
    recipients = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='Comma-separated list of phone numbers in international format'
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        help_text='SMS content (160 characters per SMS)'
    )

class SmsTemplateForm(forms.ModelForm):
    """Form for creating/editing SMS templates"""
    class Meta:
        model = SmsTemplate
        fields = ['name', 'template_key', 'content']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'template_key': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        help_texts = {
            'content': 'Use {variable} syntax for placeholders, e.g., "Hello {name}, your appointment is on {date}"'
        }

