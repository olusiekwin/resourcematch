from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('beneficiary', 'Beneficiary'),
        ('volunteer', 'Volunteer'),
        ('donor', 'Donor'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # Fields for beneficiaries
    disability_type = models.CharField(max_length=255, blank=True, null=True)
    medical_condition = models.CharField(max_length=255, blank=True, null=True)
    is_widow = models.BooleanField(default=False)
    is_elderly = models.BooleanField(default=False)
    needs_description = models.TextField(blank=True, null=True)
    
    # Fields for volunteers
    skills = models.TextField(blank=True, null=True)
    availability = models.TextField(blank=True, null=True)
    
    # Fields for donors
    preferred_categories = models.TextField(blank=True, null=True)
    
    # Common fields
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def beneficiary_category(self):
        if self.disability_type:
            return 'pwd'
        elif self.medical_condition:
            return 'medical'
        elif self.is_widow:
            return 'widows'
        elif self.is_elderly:
            return 'elderly'
        else:
            return 'other'


class Beneficiary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='beneficiary_profile')
    needs_description = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    mobility_limitations = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Beneficiary: {self.user.username}"


class Volunteer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='volunteer_profile')
    bio = models.TextField(blank=True, null=True)
    availability = models.TextField(blank=True, null=True)
    transportation_type = models.CharField(max_length=50, blank=True, null=True)
    verified = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    max_distance_km = models.IntegerField(default=10)
    
    def __str__(self):
        return f"Volunteer: {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()


@receiver(post_save, sender=UserProfile)
def create_specific_profile(sender, instance, created, **kwargs):
    if instance.user_type == 'beneficiary' and not hasattr(instance.user, 'beneficiary_profile'):
        Beneficiary.objects.create(user=instance.user)
    elif instance.user_type == 'volunteer' and not hasattr(instance.user, 'volunteer_profile'):
        Volunteer.objects.create(user=instance.user)

