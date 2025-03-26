from django import forms
from .models import Match, Feedback

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['notes', 'estimated_arrival']
        widgets = {
            'estimated_arrival': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(),
        }

