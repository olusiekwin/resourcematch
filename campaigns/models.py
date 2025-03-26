from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from datetime import timedelta


class Campaign(models.Model):
    CATEGORY_CHOICES = (
        ('pwd', 'People with Disabilities'),
        ('medical', 'Medical Conditions'),
        ('widows', 'Widows'),
        ('elderly', 'Elderly Citizens'),
        ('education', 'Education'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    image = models.ImageField(upload_to='campaign_images/', blank=True, null=True)
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    beneficiary_description = models.TextField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('campaign_detail', args=[str(self.id)])
    
    @property
    def progress_percentage(self):
        if self.goal_amount == 0:
            return 0
        return int((self.current_amount / self.goal_amount) * 100)
    
    @property
    def days_left(self):
        now = timezone.now()
        if now > self.end_date:
            return 0
        return (self.end_date - now).days
    
    @property
    def is_expired(self):
        return timezone.now() > self.end_date
    
    @property
    def donors_count(self):
        return self.donations.filter(status='completed').count()
    
    def update_status(self):
        now = timezone.now()
        if self.status == 'active' and now > self.end_date:
            self.status = 'completed'
            self.save()
        elif self.status == 'active' and self.current_amount >= self.goal_amount:
            self.status = 'completed'
            self.save()
        return self.status


class CampaignUpdate(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.campaign.title} - {self.title}"


class Donation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='donations')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.donor.username} - {self.amount} - {self.campaign.title}"
    
    def save(self, *args, **kwargs):
        # If this is a completed donation and it's a new record (no ID yet)
        if self.status == 'completed' and not self.id:
            # Update the campaign's current amount
            self.campaign.current_amount += self.amount
            self.campaign.save()
            
            # Check if the campaign has reached its goal
            if self.campaign.current_amount >= self.campaign.goal_amount:
                self.campaign.status = 'completed'
                self.campaign.save()
        
        super().save(*args, **kwargs)

