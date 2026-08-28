import os

from .base import *

# 开发模式
DEBUG = True

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('缺少开发环境变量：DJANGO_SECRET_KEY')

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'testserver',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

MEDIA_ROOT = BASE_DIR / 'media'
STATIC_ROOT = BASE_DIR / 'staticfiles'
