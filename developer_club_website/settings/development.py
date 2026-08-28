from .base import *

# 开发模式
DEBUG = True

SECRET_KEY = 'django-insecure-n*i&$o-66qcvl2f_w+wm61s+50m78zyc#yoev2$%3_)^b_8aj)'

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