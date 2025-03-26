from django.contrib import admin
from .models import Campaign, CampaignUpdate, Donation


class CampaignUpdateInline(admin.TabularInline):
    model = CampaignUpdate
    extra = 0


class DonationInline(admin.TabularInline):
    model = Donation
    extra = 0
    readonly_fields = ['donor', 'amount', 'status', 'created_at']
    fields = ['donor', 'amount', 'status', 'anonymous', 'created_at']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_by', 'goal_amount', 'current_amount', 'status', 'created_at']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['title', 'description', 'created_by__username']
    readonly_fields = ['current_amount', 'created_at', 'updated_at']
    actions = ['approve_campaigns', 'mark_as_completed', 'mark_as_featured']
    inlines = [CampaignUpdateInline, DonationInline]
    
    def approve_campaigns(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"{queryset.count()} campaigns have been approved.")
    approve_campaigns.short_description = "Approve selected campaigns"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} campaigns have been marked as completed.")
    mark_as_completed.short_description = "Mark selected campaigns as completed"
    
    def mark_as_featured(self, request, queryset):
        # First, remove featured status from all campaigns
        Campaign.objects.update(is_featured=False)
        
        # Then set featured status for selected campaigns
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} campaigns have been marked as featured.")
    mark_as_featured.short_description = "Mark selected campaigns as featured"


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['donor', 'campaign', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'anonymous']
    search_fields = ['donor__username', 'campaign__title', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_as_completed', 'mark_as_refunded']
    
    def mark_as_completed(self, request, queryset):
        for donation in queryset:
            if donation.status != 'completed':
                # Update campaign amount only if status is changing to completed
                donation.status = 'completed'
                donation.save()  # This will trigger the save method in the model
        
        self.message_user(request, f"{queryset.count()} donations have been marked as completed.")
    mark_as_completed.short_description = "Mark selected donations as completed"
    
    def mark_as_refunded(self, request, queryset):
        for donation in queryset:
            if donation.status == 'completed':
                # Reduce campaign amount if donation was previously completed
                donation.campaign.current_amount -= donation.amount
                donation.campaign.save()
            
            donation.status = 'refunded'
            donation.save()
        
        self.message_user(request, f"{queryset.count()} donations have been marked as refunded.")
    mark_as_refunded.short_description = "Mark selected donations as refunded"

