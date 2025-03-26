from django.db import models
from accounts.models import User, Beneficiary, Volunteer

class ResourceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # CSS class for icon
    
    def __str__(self):
        return self.name

class Resource(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('requested', 'Requested'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    resource_type = models.ForeignKey(ResourceType, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # For resources offered by volunteers
    offered_by = models.ForeignKey(Volunteer, on_delete=models.SET_NULL, null=True, blank=True, related_name='offered_resources')
    
    # For resources requested by beneficiaries
    requested_by = models.ForeignKey(Beneficiary, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_resources')
    
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

