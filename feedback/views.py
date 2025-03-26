from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Feedback
from .forms import FeedbackForm

@login_required
def feedback_list(request):
    # Admins can see all feedback, users can only see their own
    if request.user.is_staff:
        feedbacks = Feedback.objects.all().order_by('-created_at')
    else:
        feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'feedback/feedback_list.html', {'feedbacks': feedbacks})

@login_required
def create_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, 'Feedback submitted successfully.')
            return redirect('feedback_list')
    else:
        form = FeedbackForm()
    
    return render(request, 'feedback/create_feedback.html', {'form': form})

@login_required
def feedback_detail(request, feedback_id):
    # Admins can see all feedback, users can only see their own
    if request.user.is_staff:
        feedback = get_object_or_404(Feedback, id=feedback_id)
    else:
        feedback = get_object_or_404(Feedback, id=feedback_id, user=request.user)
    
    return render(request, 'feedback/feedback_detail.html', {'feedback': feedback})

