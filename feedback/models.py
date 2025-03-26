from django.db import models
from django.contrib.auth.models import User

class Feedback(models.Model):
    RATING_CHOICES = (
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    title = models.CharField(max_length=100)
    content = models.TextField()
    rating = models.IntegerField(choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback from {self.user.username}: {self.rating}/5"

