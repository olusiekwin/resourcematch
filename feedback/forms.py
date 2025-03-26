from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['title', 'content', 'rating']
        widgets = {
            'rating': forms.RadioSelect(),
        }

