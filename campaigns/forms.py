from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import Campaign, CampaignUpdate, Donation


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = [
            'title', 'category', 'description', 'goal_amount', 
            'end_date', 'image', 'location', 'beneficiary_description'
        ]
        widgets = {
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'beneficiary_description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if end_date:
            # Convert to datetime with time component
            if isinstance(end_date, timezone.datetime):
                end_datetime = end_date
            else:
                end_datetime = timezone.datetime.combine(
                    end_date, 
                    timezone.datetime.min.time(),
                    tzinfo=timezone.get_current_timezone()
                )
            
            # Check if end date is in the future
            if end_datetime <= timezone.now():
                raise forms.ValidationError("End date must be in the future.")
            
            # Check if campaign duration is reasonable (e.g., not more than 1 year)
            max_duration = timezone.now() + timedelta(days=365)
            if end_datetime > max_duration:
                raise forms.ValidationError("Campaign duration cannot exceed 1 year.")
            
            return end_datetime
        return end_date


class CampaignUpdateForm(forms.ModelForm):
    class Meta:
        model = CampaignUpdate
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['amount', 'message', 'anonymous']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Leave a message of support (optional)'}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Donation amount must be greater than zero.")
        return amount

