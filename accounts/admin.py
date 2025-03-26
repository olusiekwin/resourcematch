from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Beneficiary, Volunteer

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'user profile'

class BeneficiaryInline(admin.StackedInline):
    model = Beneficiary
    can_delete = False
    verbose_name_plural = 'beneficiary'

class VolunteerInline(admin.StackedInline):
    model = Volunteer
    can_delete = False
    verbose_name_plural = 'volunteer'

class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type', 'is_staff')
    list_filter = ('userprofile__user_type', 'is_staff', 'is_superuser', 'is_active')
    
    def get_user_type(self, obj):
        return obj.userprofile.get_user_type_display() if hasattr(obj, 'userprofile') else '-'
    get_user_type.short_description = 'User Type'
    
    def get_inlines(self, request, obj=None):
        if obj:
            if hasattr(obj, 'userprofile'):
                if obj.userprofile.user_type == 'beneficiary':
                    return [UserProfileInline, BeneficiaryInline]
                elif obj.userprofile.user_type == 'volunteer':
                    return [UserProfileInline, VolunteerInline]
        return [UserProfileInline]

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'emergency_contact_name', 'mobility_limitations')
    search_fields = ('user__username', 'user__email', 'emergency_contact_name')

@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('user', 'transportation_type', 'verified', 'active', 'max_distance_km')
    list_filter = ('verified', 'active')
    search_fields = ('user__username', 'user__email', 'bio')

