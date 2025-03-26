from django.db import models
from django.utils import timezone
from accounts.models import Beneficiary, Volunteer

class ResourceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, help_text="Bootstrap icon name (e.g., 'bi-house')")
    color = models.CharField(max_length=20, default="#0d6efd", help_text="Color code for category")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Resource Categories"

class ResourceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(ResourceCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="resource_types")
    icon = models.CharField(max_length=50, help_text="Bootstrap icon name (e.g., 'bi-house')")
    
    def __str__(self):
        return self.name

class Resource(models.Model):
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('available', 'Available'),
        ('matched', 'Matched'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    resource_type = models.ForeignKey(ResourceType, on_delete=models.CASCADE, related_name="resources")
    category = models.ForeignKey(ResourceCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="resources")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    quantity = models.PositiveIntegerField(default=1)
    requested_by = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, null=True, blank=True, related_name="requested_resources")
    offered_by = models.ForeignKey(Volunteer, on_delete=models.CASCADE, null=True, blank=True, related_name="offered_resources")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='resources/', null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    is_urgent = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.title
    
    def is_expired(self):
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False
    
    def days_remaining(self):
        if self.expiry_date:
            delta = self.expiry_date - timezone.now()
            return max(0, delta.days)
        return None
    
    def save(self, *args, **kwargs):
        # Set category based on resource type if not provided
        if not self.category and self.resource_type and self.resource_type.category:
            self.category = self.resource_type.category
        super().save(*args, **kwargs)

