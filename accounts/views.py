from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Beneficiary, Volunteer
from .forms import UserRegistrationForm, UserProfileForm, BeneficiaryProfileForm, VolunteerProfileForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    user = request.user
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=user)
        
        if user.user_type == 'beneficiary':
            profile_form = BeneficiaryProfileForm(request.POST, instance=user.beneficiary_profile)
        elif user.user_type == 'volunteer':
            profile_form = VolunteerProfileForm(request.POST, instance=user.volunteer_profile)
        else:
            profile_form = None
        
        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=user)
        
        if user.user_type == 'beneficiary':
            profile_form = BeneficiaryProfileForm(instance=user.beneficiary_profile)
        elif user.user_type == 'volunteer':
            profile_form = VolunteerProfileForm(instance=user.volunteer_profile)
        else:
            profile_form = None
    
    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def dashboard(request):
    user = request.user
    
    if user.user_type == 'beneficiary':
        # Get beneficiary's requested resources and matches
        requested_resources = user.beneficiary_profile.requested_resources.all()
        matches = user.beneficiary_profile.beneficiary_matches.all()
        
        return render(request, 'accounts/beneficiary_dashboard.html', {
            'requested_resources': requested_resources,
            'matches': matches
        })
    
    elif user.user_type == 'volunteer':
        # Get volunteer's offered resources and matches
        offered_resources = user.volunteer_profile.offered_resources.all()
        matches = user.volunteer_profile.volunteer_matches.all()
        
        return render(request, 'accounts/volunteer_dashboard.html', {
            'offered_resources': offered_resources,
            'matches': matches
        })
    
    else:  # Admin
        return render(request, 'accounts/admin_dashboard.html')

@login_required
def volunteer_list(request):
    volunteers = Volunteer.objects.filter(active=True)
    return render(request, 'accounts/volunteer_list.html', {'volunteers': volunteers})

@login_required
def volunteer_detail(request, volunteer_id):
    volunteer = get_object_or_404(Volunteer, id=volunteer_id)
    return render(request, 'accounts/volunteer_detail.html', {'volunteer': volunteer})

@login_required
def beneficiary_list(request):
    # Only volunteers and admins can see the list of beneficiaries
    if request.user.user_type not in ['volunteer', 'admin']:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    beneficiaries = Beneficiary.objects.all()
    return render(request, 'accounts/beneficiary_list.html', {'beneficiaries': beneficiaries})

@login_required
def beneficiary_detail(request, beneficiary_id):
    # Only volunteers, admins, and the beneficiary themselves can see the details
    beneficiary = get_object_or_404(Beneficiary, id=beneficiary_id)
    
    if request.user.user_type not in ['volunteer', 'admin'] and request.user != beneficiary.user:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    return render(request, 'accounts/beneficiary_detail.html', {'beneficiary': beneficiary})

