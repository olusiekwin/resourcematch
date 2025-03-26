from django.urls import path, include

urlpatterns = [
    path('accounts/', include('accounts.api_urls')),
    path('resources/', include('resources.api_urls')),
    path('matches/', include('matches.api_urls')),
    path('feedback/', include('feedback.api_urls')),
    path('campaigns/', include('campaigns.api_urls')),
    path('sms/', include('sms.api_urls')),
]

