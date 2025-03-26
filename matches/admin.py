from django.contrib import admin
from .models import Match, Feedback

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'resource', 'beneficiary', 'volunteer', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('resource__name', 'beneficiary__user__username', 'volunteer__user__username')
    date_hierarchy = 'created_at'

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'match', 'rating', 'is_from_beneficiary', 'created_at')
    list_filter = ('rating', 'is_from_beneficiary', 'created_at')
    search_fields = ('comment', 'match__resource__name')

