from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from resources.views import home

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Home page
    path('', home, name='home'),
    
    # App URLs
    path('', include('accounts.urls')),
    path('', include('resources.urls')),
    path('', include('matches.urls')),
    path('', include('feedback.urls')),
    path('', include('notifications.urls')),
    path('', include('campaigns.urls')),
    path('', include('sms_integration.urls')),
    
    # API URLs
    path('api/', include('resourcematch.api_urls')),
    path('api/accounts/', include('accounts.api_urls')),
    path('api/resources/', include('resources.api_urls')),
    
    # Static pages
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('faq/', TemplateView.as_view(template_name='faq.html'), name='faq'),
    path('how-it-works/', TemplateView.as_view(template_name='how_it_works.html'), name='how_it_works'),
    path('impact/', TemplateView.as_view(template_name='impact.html'), name='impact'),
    path('partners/', TemplateView.as_view(template_name='partners.html'), name='partners'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

