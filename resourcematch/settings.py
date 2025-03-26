# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'campaigns',
    'notifications',
]

# Add to TEMPLATES context_processors
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notifications',  # Add this line
            ],
        },
    },
]

