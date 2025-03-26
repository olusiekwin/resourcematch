from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('title', 'content', 'user__username')

