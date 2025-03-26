from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Beneficiary, Volunteer

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    user_type = forms.ChoiceField(choices=UserProfile.USER_TYPE_CHOICES)
    phone_number = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 
                  'user_type', 'phone_number', 'address']
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
            # Update user profile
            profile = user.userprofile
            profile.user_type = self.cleaned_data['user_type']
            profile.phone_number = self.cleaned_data['phone_number']
            profile.address = self.cleaned_data['address']
            profile.save()
            
            # Create specific profile based on user type
            if profile.user_type == 'beneficiary':
                if not hasattr(user, 'beneficiary_profile'):
                    Beneficiary.objects.create(user=user)
            elif profile.user_type == 'volunteer':
                if not hasattr(user, 'volunteer_profile'):
                    Volunteer.objects.create(user=user)
                    
        return user

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'bio', 'profile_picture']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Update user fields
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile.save()
            
        return profile

class BeneficiaryProfileForm(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = ['needs_description', 'emergency_contact_name', 
                  'emergency_contact_phone', 'mobility_limitations']

class VolunteerProfileForm(forms.ModelForm):
    class Meta:
        model = Volunteer
        fields = ['bio', 'availability', 'transportation_type', 'max_distance_km']
        widgets = {
            'availability': forms.HiddenInput(),  # Will be handled by JavaScript
        }

