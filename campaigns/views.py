from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import Campaign, CampaignUpdate, Donation
from .forms import CampaignForm, CampaignUpdateForm, DonationForm
from accounts.models import UserProfile
from notifications.utils import create_notification

import csv
import datetime


def campaign_list(request):
    campaigns = Campaign.objects.filter(status='active')
    
    # Filter by category
    selected_category = request.GET.get('category')
    if selected_category:
        campaigns = campaigns.filter(category=selected_category)
    
    # Filter by status
    selected_status = request.GET.get('status')
    if selected_status:
        if selected_status == 'urgent':
            # Urgent campaigns are those with less than 7 days left
            seven_days_from_now = timezone.now() + datetime.timedelta(days=7)
            campaigns = campaigns.filter(end_date__lte=seven_days_from_now)
        else:
            campaigns = campaigns.filter(status=selected_status)
    
    # Sort campaigns
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'newest':
        campaigns = campaigns.order_by('-created_at')
    elif sort_by == 'ending_soon':
        campaigns = campaigns.order_by('end_date')
    elif sort_by == 'most_funded':
        campaigns = campaigns.order_by('-current_amount')
    elif sort_by == 'least_funded':
        campaigns = campaigns.order_by('current_amount')
    
    # Get featured campaign
    featured_campaign = Campaign.objects.filter(is_featured=True, status='active').first()
    
    # Paginate results
    paginator = Paginator(campaigns, 9)  # Show 9 campaigns per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'campaigns': page_obj,
        'featured_campaign': featured_campaign,
        'selected_category': selected_category,
        'selected_status': selected_status,
        'sort_by': sort_by,
    }
    
    return render(request, 'campaigns/campaign_list.html', context)


def campaign_detail(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Update campaign status if needed
    campaign.update_status()
    
    # Get recent donations
    recent_donations = campaign.donations.filter(status='completed', anonymous=False).order_by('-created_at')[:5]
    
    # Get similar campaigns
    similar_campaigns = Campaign.objects.filter(
        category=campaign.category, 
        status='active'
    ).exclude(id=campaign.id).order_by('-created_at')[:3]
    
    context = {
        'campaign': campaign,
        'recent_donations': recent_donations,
        'similar_campaigns': similar_campaigns,
    }
    
    return render(request, 'campaigns/campaign_detail.html', context)


@login_required
def create_campaign(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.created_by = request.user
            campaign.save()
            
            # Create notification for admin
            create_notification(
                recipient=None,  # Admin notification
                title="New Campaign Created",
                message=f"A new campaign '{campaign.title}' has been created and needs approval.",
                link=reverse('admin:campaigns_campaign_change', args=[campaign.id]),
                is_admin=True
            )
            
            messages.success(request, "Your campaign has been created and is pending approval.")
            return redirect('donor_dashboard')
    else:
        form = CampaignForm()
    
    return render(request, 'campaigns/create_campaign.html', {'form': form})


@login_required
def edit_campaign(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Check if user is the campaign creator
    if request.user != campaign.created_by:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_detail', campaign_id=campaign.id)
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully.")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/edit_campaign.html', {'form': form, 'campaign': campaign})


@login_required
def add_campaign_update(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Check if user is the campaign creator
    if request.user != campaign.created_by:
        messages.error(request, "You don't have permission to add updates to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign.id)
    
    if request.method == 'POST':
        form = CampaignUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.campaign = campaign
            update.save()
            
            # Create notifications for donors
            donors = User.objects.filter(
                donations__campaign=campaign, 
                donations__status='completed'
            ).distinct()
            
            for donor in donors:
                create_notification(
                    recipient=donor,
                    title=f"Update on {campaign.title}",
                    message=f"New update: {update.title}",
                    link=reverse('campaign_detail', args=[campaign.id]),
                )
            
            messages.success(request, "Campaign update added successfully.")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignUpdateForm()
    
    return render(request, 'campaigns/add_campaign_update.html', {'form': form, 'campaign': campaign})


@login_required
def make_donation(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Check if campaign is active
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting donations.")
        return redirect('campaign_detail', campaign_id=campaign.id)
    
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.campaign = campaign
            donation.donor = request.user
            
            # Process payment (simplified for this example)
            # In a real application, you would integrate with a payment gateway
            card_number = request.POST.get('card_number', '').replace(' ', '')
            donation.card_last_four = card_number[-4:] if len(card_number) >= 4 else '0000'
            donation.transaction_id = f"TX-{timezone.now().strftime('%Y%m%d%H%M%S')}-{request.user.id}"
            donation.status = 'completed'  # Assume payment is successful
            
            donation.save()  # This will also update the campaign's current amount
            
            # Create notification for campaign creator
            create_notification(
                recipient=campaign.created_by,
                title="New Donation Received",
                message=f"Your campaign '{campaign.title}' received a donation of {donation.amount}.",
                link=reverse('campaign_detail', args=[campaign.id]),
            )
            
            # Create notification for donor
            create_notification(
                recipient=request.user,
                title="Donation Successful",
                message=f"Your donation of {donation.amount} to '{campaign.title}' was successful.",
                link=reverse('donation_detail', args=[donation.id]),
            )
            
            return redirect('donation_success', donation_id=donation.id)
    else:
        form = DonationForm()
    
    return render(request, 'donations/make_donation.html', {'form': form, 'campaign': campaign})


@login_required
def donation_success(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id, donor=request.user)
    return render(request, 'donations/donation_success.html', {'donation': donation})


@login_required
def donation_detail(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id, donor=request.user)
    return render(request, 'donations/donation_detail.html', {'donation': donation})


@login_required
def download_receipt(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id, donor=request.user)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="donation_receipt_{donation.id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Donation Receipt'])
    writer.writerow([''])
    writer.writerow(['Donation ID', donation.id])
    writer.writerow(['Date', donation.created_at.strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Donor', donation.donor.get_full_name() or donation.donor.username])
    writer.writerow(['Campaign', donation.campaign.title])
    writer.writerow(['Amount', donation.amount])
    writer.writerow(['Status', donation.get_status_display()])
    writer.writerow(['Transaction ID', donation.transaction_id])
    
    return response


@login_required
def donor_dashboard(request):
    # Check if user is a donor
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'donor':
        messages.error(request, "You don't have access to the donor dashboard.")
        return redirect('home')
    
    # Get user's donations
    donations = Donation.objects.filter(donor=request.user).order_by('-created_at')
    
    # Get user's campaigns
    campaigns = Campaign.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Calculate total donated
    total_donated = donations.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Count unique beneficiaries helped
    beneficiaries_helped = campaigns.filter(status__in=['active', 'completed']).count()
    
    # Get featured campaigns for sidebar
    featured_campaigns = Campaign.objects.filter(is_featured=True, status='active').order_by('-created_at')[:3]
    
    context = {
        'donations': donations,
        'campaigns': campaigns,
        'total_donated': total_donated,
        'beneficiaries_helped': beneficiaries_helped,
        'featured_campaigns': featured_campaigns,
    }
    
    return render(request, 'accounts/donor_dashboard.html', context)


def beneficiary_categories(request):
    return render(request, 'resources/beneficiary_categories.html')

