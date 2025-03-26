from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Beneficiary, Volunteer

class BeneficiaryInline(admin.StackedInline):
    model = Beneficiary
    can_delete = False
    verbose_name_plural = 'beneficiary'

class VolunteerInline(admin.StackedInline):
    model = Volunteer
    can_delete = False
    verbose_name_plural = 'volunteer'

class UserAdmin(BaseUserAdmin):
    inlines = []
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'address', 'latitude', 'longitude')}),
    )
    
    def get_inlines(self, request, obj=None):
        if obj:
            if obj.user_type == 'beneficiary':
                return [BeneficiaryInline]
            elif obj.user_type == 'volunteer':
                return [VolunteerInline]
        return []

admin.site.register(User, UserAdmin)
admin.site.register(Beneficiary)
admin.site.register(Volunteer)

