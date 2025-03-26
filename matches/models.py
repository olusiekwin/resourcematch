from django.db import models
from accounts.models import Beneficiary, Volunteer
from resources.models import Resource

class Match(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    resource = models.OneToOneField(Resource, on_delete=models.CASCADE, related_name='match')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='beneficiary_matches')
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, related_name='volunteer_matches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Match {self.id}: {self.resource.name} - {self.status}"

class Feedback(models.Model):
    RATING_CHOICES = (
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    )
    
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    is_from_beneficiary = models.BooleanField()  # True if feedback is from beneficiary, False if from volunteer
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        from_user = "Beneficiary" if self.is_from_beneficiary else "Volunteer"
        return f"Feedback from {from_user} for Match {self.match.id}: {self.rating}/5"

