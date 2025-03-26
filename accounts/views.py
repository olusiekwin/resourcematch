from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile, Beneficiary, Volunteer
from .forms import UserRegistrationForm, UserProfileForm, BeneficiaryProfileForm, VolunteerProfileForm
from resources.models import Resource
from matches.models import Match

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

def register_beneficiary(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        beneficiary_form = BeneficiaryProfileForm(request.POST)
        
        if form.is_valid() and beneficiary_form.is_valid():
            # Set user type to beneficiary
            form.cleaned_data['user_type'] = 'beneficiary'
            user = form.save()
            
            # Update beneficiary profile
            beneficiary = user.beneficiary_profile
            beneficiary.needs_description = beneficiary_form.cleaned_data['needs_description']
            beneficiary.emergency_contact_name = beneficiary_form.cleaned_data['emergency_contact_name']
            beneficiary.emergency_contact_phone = beneficiary_form.cleaned_data['emergency_contact_phone']
            beneficiary.mobility_limitations = beneficiary_form.cleaned_data['mobility_limitations']
            beneficiary.save()
            
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm(initial={'user_type': 'beneficiary'})
        beneficiary_form = BeneficiaryProfileForm()
    
    return render(request, 'accounts/register_beneficiary.html', {
        'form': form,
        'beneficiary_form': beneficiary_form
    })

def register_volunteer(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        volunteer_form = VolunteerProfileForm(request.POST)
        
        if form.is_valid() and volunteer_form.is_valid():
            # Set user type to volunteer
            form.cleaned_data['user_type'] = 'volunteer'
            user = form.save()
            
            # Update volunteer profile
            volunteer = user.volunteer_profile
            volunteer.bio = volunteer_form.cleaned_data['bio']
            volunteer.availability = volunteer_form.cleaned_data['availability']
            volunteer.transportation_type = volunteer_form.cleaned_data['transportation_type']
            volunteer.max_distance_km = volunteer_form.cleaned_data['max_distance_km']
            volunteer.save()
            
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm(initial={'user_type': 'volunteer'})
        volunteer_form = VolunteerProfileForm()
    
    return render(request, 'accounts/register_volunteer.html', {
        'form': form,
        'volunteer_form': volunteer_form
    })

@login_required
def profile(request):
    user = request.user
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=user.userprofile)
        
        if user.userprofile.user_type == 'beneficiary':
            profile_form = BeneficiaryProfileForm(request.POST, instance=user.beneficiary_profile)
        elif user.userprofile.user_type == 'volunteer':
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
        user_form = UserProfileForm(instance=user.userprofile)
        
        if user.userprofile.user_type == 'beneficiary':
            profile_form = BeneficiaryProfileForm(instance=user.beneficiary_profile)
        elif user.userprofile.user_type == 'volunteer':
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
    
    if user.userprofile.user_type == 'beneficiary':
        # Get beneficiary's requested resources and matches
        requested_resources = Resource.objects.filter(requested_by=user.beneficiary_profile)
        matches = Match.objects.filter(beneficiary=user.beneficiary_profile)
        
        # Get nearby resources
        nearby_resources = []
        if user.userprofile.latitude and user.userprofile.longitude:
            # In a real app, you would use a spatial query here
            nearby_resources = Resource.objects.filter(status='available')[:5]
        
        return render(request, 'accounts/beneficiary_dashboard.html', {
            'requested_resources': requested_resources,
            'matches': matches,
            'nearby_resources': nearby_resources
        })
    
    elif user.userprofile.user_type == 'volunteer':
        # Get volunteer's offered resources and matches
        offered_resources = Resource.objects.filter(offered_by=user.volunteer_profile)
        matches = Match.objects.filter(volunteer=user.volunteer_profile)
        
        # Get nearby resource requests
        nearby_requests = []
        if user.userprofile.latitude and user.userprofile.longitude:
            # In a real app, you would use a spatial query here
            nearby_requests = Resource.objects.filter(status='requested')[:5]
        
        return render(request, 'accounts/volunteer_dashboard.html', {
            'offered_resources': offered_resources,
            'matches': matches,
            'nearby_requests': nearby_requests
        })
    
    elif user.userprofile.user_type == 'donor':
        # Redirect to donor dashboard in campaigns app
        return redirect('donor_dashboard')
    
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
    if request.user.userprofile.user_type not in ['volunteer', 'admin'] and not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    beneficiaries = Beneficiary.objects.all()
    return render(request, 'accounts/beneficiary_list.html', {'beneficiaries': beneficiaries})

@login_required
def beneficiary_detail(request, beneficiary_id):
    # Only volunteers, admins, and the beneficiary themselves can see the details
    beneficiary = get_object_or_404(Beneficiary, id=beneficiary_id)
    
    if (request.user.userprofile.user_type not in ['volunteer', 'admin'] and 
        not request.user.is_staff and 
        request.user != beneficiary.user):
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    return render(request, 'accounts/beneficiary_detail.html', {'beneficiary': beneficiary})

