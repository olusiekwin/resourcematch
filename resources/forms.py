from django import forms
from .models import Resource, ResourceType, ResourceCategory

class ResourceTypeForm(forms.ModelForm):
    class Meta:
        model = ResourceType
        fields = ['name', 'description', 'icon', 'category']

class ResourceCategoryForm(forms.ModelForm):
    class Meta:
        model = ResourceCategory
        fields = ['name', 'description', 'icon', 'color']

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'resource_type', 'category', 'description', 'quantity', 
                  'image', 'latitude', 'longitude', 'address', 'city', 'state', 
                  'postal_code', 'country', 'is_urgent', 'expiry_date']
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ResourceRequestForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'resource_type', 'description', 'quantity', 
                  'image', 'address', 'city', 'state', 'postal_code', 
                  'country', 'is_urgent', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        
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
        fields = ['title', 'resource_type', 'description', 'quantity', 
                  'image', 'address', 'city', 'state', 'postal_code', 
                  'country', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        
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

class ResourceSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={
            'placeholder': 'Search resources...',
            'class': 'form-control',
        })
    )
    
    resource_type = forms.ModelChoiceField(
        queryset=ResourceType.objects.all(),
        required=False,
        label="Resource Type",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ModelChoiceField(
        queryset=ResourceCategory.objects.all(),
        required=False,
        label="Category",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(Resource.STATUS_CHOICES),
        required=False,
        label="Status",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort = forms.ChoiceField(
        choices=[
            ('newest', 'Newest First'),
            ('oldest', 'Oldest First'),
            ('name_asc', 'Name A-Z'),
            ('name_desc', 'Name Z-A'),
        ],
        required=False,
        initial='newest',
        label="Sort By",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

