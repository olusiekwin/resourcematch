from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Beneficiary, Volunteer

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 
                  'phone_number', 'address']
        
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Create profile based on user type
            if user.user_type == 'beneficiary':
                Beneficiary.objects.create(user=user)
            elif user.user_type == 'volunteer':
                Volunteer.objects.create(user=user)
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']

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

