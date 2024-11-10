"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 4.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os, random, string
from pathlib import Path
from dotenv import load_dotenv
from str2bool import str2bool

load_dotenv()  # take environment variables from .env.

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = ''.join(random.choice( string.ascii_lowercase  ) for i in range( 32 ))

# Enable/Disable DEBUG Mode
DEBUG = str2bool(os.environ.get('DEBUG'))
from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)
#print(' DEBUG -> ' + str(DEBUG) ) 

# Maximum size of uploaded file
DATA_UPLOAD_MAX_MEMORY_SIZE = 209715200  # 200MB in bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 209715200  # 200MB in bytes

# Timeout settings
TIMEOUT = 600

# Docker HOST
ALLOWED_HOSTS = [
    '*', 
    'fu2uregym.com', 
    'www.fu2uregym.com', 
    '3.121.13.73', 
    'ec2-3-121-13-73.eu-central-1.compute.amazonaws.com'
]

# Add here your deployment HOSTS
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000', 
    'http://localhost:5085', 
    'http://127.0.0.1:8000', 
    'http://127.0.0.1:5085', 
    'http://fu2uregym.com', 
    'http://www.fu2uregym.com', 
    'https://fu2uregym.com', 
    'https://www.fu2uregym.com',
    'http://3.121.13.73',
    'https://3.121.13.73',
    'http://ec2-3-121-13-73.eu-central-1.compute.amazonaws.com',
    'https://ec2-3-121-13-73.eu-central-1.compute.amazonaws.com'
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:    
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.apple',

    "artwork",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "core.urls"

HOME_TEMPLATES = os.path.join(BASE_DIR, 'artwork', 'templates')

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [HOME_TEMPLATES],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DB_ENGINE   = os.getenv('DB_ENGINE'   , None)
DB_USERNAME = os.getenv('DB_USERNAME' , None)
DB_PASS     = os.getenv('DB_PASS'     , None)
DB_HOST     = os.getenv('DB_HOST'     , None)
DB_PORT     = os.getenv('DB_PORT'     , None)
DB_NAME     = os.getenv('DB_NAME'     , None)

# if DB_ENGINE and DB_NAME and DB_USERNAME:
#     DATABASES = { 
#       'default': {
#         'ENGINE'  : 'django.db.backends.' + DB_ENGINE, 
#         'NAME'    : DB_NAME,
#         'USER'    : DB_USERNAME,
#         'PASSWORD': DB_PASS,
#         'HOST'    : DB_HOST,
#         'PORT'    : DB_PORT,
#         }, 
#     }
# else:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': 'db.sqlite3',
#         }
#     }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'artwork',
        'USER': 'root',
        'PASSWORD': 'artwork1234',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

#if not DEBUG:
#    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = '/'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'apple': {
        'SCOPE': [
            'email',
            'name',
        ],
        'AUTH_PARAMS': {
            'response_type': 'code id_token',
        }
    }
}

LOGIN_REDIRECT_URL = '/social-login-success/'

AUTH_USER_MODEL = 'artwork.User'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

os.makedirs(os.path.join(MEDIA_ROOT, 'post_videos'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'post_thumbnails'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'post_qr_codes'), exist_ok=True)