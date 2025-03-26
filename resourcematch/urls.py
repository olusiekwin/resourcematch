from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # App URLs
    path('accounts/', include('accounts.urls')),
    path('resources/', include('resources.urls')),
    path('matches/', include('matches.urls')),
    path('feedback/', include('feedback.urls')),
    path('notifications/', include('notifications.urls')),
    path('campaigns/', include('campaigns.urls')),
    path('sms/', include('sms.urls')),
    
    # API URLs
    path('api/', include('resourcematch.api_urls')),
    
    # Static pages
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('faq/', TemplateView.as_view(template_name='faq.html'), name='faq'),
    path('how-it-works/', TemplateView.as_view(template_name='how_it_works.html'), name='how_it_works'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

