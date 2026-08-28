import os

from .base import *


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f'缺少必要环境变量：{name}')
    return value


def env_list(name):
    return [
        item.strip()
        for item in required_env(name).split(',')
        if item.strip()
    ]


DEBUG = False
SECRET_KEY = required_env('DJANGO_SECRET_KEY')

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': required_env('DB_NAME'),
        'USER': required_env('DB_USER'),
        'PASSWORD': required_env('DB_PASSWORD'),
        'HOST': required_env('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}

STATIC_ROOT = required_env('DJANGO_STATIC_ROOT')
MEDIA_ROOT = required_env('DJANGO_MEDIA_ROOT')
PRIVATE_MEDIA_ROOT = required_env('DJANGO_PRIVATE_MEDIA_ROOT')

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
