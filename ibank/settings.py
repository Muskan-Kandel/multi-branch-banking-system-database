import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'temp'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = ['django.contrib.staticfiles']

ROOT_URLCONF = 'ibank.urls'  

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend/templates'],
        'APP_DIRS': False,
    },
]

WSGI_APPLICATION = 'ibank.wsgi.application'

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'frontend/static',
    BASE_DIR / 'frontend/extras',
]