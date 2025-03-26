from django import forms
from .models import Resource, ResourceType

class ResourceTypeForm(forms.ModelForm):
    class Meta:
        model = ResourceType
        fields = ['name', 'description', 'icon']

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['resource_type', 'name', 'description', 'quantity', 'latitude', 'longitude']
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

class ResourceRequestForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['resource_type', 'name', 'description', 'quantity']
        
    def __init__(self, *args, **kwargs):
        self.beneficiary = kwargs.pop('beneficiary', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        resource = super().save(commit=False)
        resource.status = 'requested'
        if self.beneficiary:
            resource.requested_by = self.beneficiary
            # Use beneficiary's location if available
            if self.beneficiary.user.userprofile.latitude and self.beneficiary.user.userprofile.longitude:
                resource.latitude = self.beneficiary.user.userprofile.latitude
                resource.longitude = self.beneficiary.user.userprofile.longitude
        if commit:
            resource.save()
        return resource

class ResourceOfferForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['resource_type', 'name', 'description', 'quantity']
        
    def __init__(self, *args, **kwargs):
        self.volunteer = kwargs.pop('volunteer', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        resource = super().save(commit=False)
        resource.status = 'available'
        if self.volunteer:
            resource.offered_by = self.volunteer
            # Use volunteer's location if available
            if self.volunteer.user.userprofile.latitude and self.volunteer.user.userprofile.longitude:
                resource.latitude = self.volunteer.user.userprofile.latitude
                resource.longitude = self.volunteer.user.userprofile.longitude
        if commit:
            resource.save()
        return resource

