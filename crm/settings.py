"""
Django settings for crm project.
"""

from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured
import sys

# ====================== BASE SETTINGS ======================

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your_secret_key_here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']  # For development only

# ====================== APPLICATION DEFINITION ======================

INSTALLED_APPS = [
    'django.contrib.sites'
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your apps
    'settings',
    'common',
    'massmail',
    'crm',
    'tasks',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'crm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'crm.context_processors.crm_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'crm.wsgi.application'

# ====================== DATABASE ======================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'crm_db',
        'USER': 'crm_user',
        'PASSWORD': 'Dhruva123#',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ====================== PASSWORD VALIDATION ======================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# ====================== INTERNATIONALIZATION ======================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ====================== STATIC AND MEDIA FILES ======================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "compiled_static"

if 'STATICFILES_DIRS' in locals() and STATIC_ROOT in STATICFILES_DIRS:
    raise ImproperlyConfigured("STATIC_ROOT cannot be in STATICFILES_DIRS")

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ====================== DEFAULT PRIMARY KEY ======================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ====================== CRM SPECIFIC SETTINGS ======================

SECRET_CRM_PREFIX = 'crm/'
FIRST_STEP = True

KEEP_TICKET = "Ticket: %s"
NOT_ALLOWED_EMAILS = []

CONVERT_REQUIRED_FIELDS = ['name', 'email', 'phone', 'company']
NO_NAME_STR = 'Unnamed'

# ====================== EMAIL SETTINGS ======================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@example.com'
EMAIL_HOST_PASSWORD = 'your_email_password'

# IMAP Settings
IMAP_CONNECTION_IDLE = 300
IMAP_NOOP_PERIOD = 300
REUSE_IMAP_CONNECTION = False

# Recaptcha
GOOGLE_RECAPTCHA_SITE_KEY = ''
GOOGLE_RECAPTCHA_SECRET_KEY = ''

# GeoIP
GEOIP = False

# OAuth2 Configuration
OAUTH2_DATA = {
    'gmail.com': {
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://accounts.google.com/o/oauth2/token',
        'client_id': '',
        'client_secret': '',
        'scope': 'https://mail.google.com/',
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
    },
    'smtp.gmail.com': {
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://accounts.google.com/o/oauth2/token',
        'client_id': '',
        'client_secret': '',
        'scope': 'https://mail.google.com/',
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
    }
}

# CRM Columns
CONTACT_COLUMNS = ['name', 'email', 'phone', 'company', 'created_on']
COMPANY_COLUMNS = ['name', 'industry', 'phone', 'email', 'website']
LEAD_COLUMNS = [('id','ID'), ('name','Name'), ('email','Email'), ('status','Status')]
DEAL_COLUMNS = [('id','ID'), ('name','Name'), ('amount','Amount'), ('stage','Stage'), ('created_on','Created Date')]

# Task Settings
TASK_DEFAULT_STATUS = 'New'
TASK_PRIORITY_CHOICES = [('low','Low'), ('medium','Medium'), ('high','High')]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler',},
        'file': {'class': 'logging.FileHandler','filename': BASE_DIR / 'debug.log',},
    },
    'root': {'handlers': ['console','file'],'level':'INFO',},
    'loggers': {
        'django': {'handlers':['console','file'],'level':os.getenv('DJANGO_LOG_LEVEL','INFO'),'propagate':False,},
        'crm': {'handlers':['console','file'],'level':'DEBUG',},
    },
}

# Security (production)
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO','https')
    SECURE_REFERRER_POLICY = 'same-origin'

# ====================== TESTING PATCH ======================

if 'test' in sys.argv:
    # Use in-memory email backend
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    # Lazy patching to avoid AppRegistryNotReady
    def patch_massmail_for_tests():
        try:
            from massmail.utils import sendmassmail
            import threading

            # Dummy send function
            def dummy_send_massmail(*args, **kwargs):
                return None

            sendmassmail.send_massmail = dummy_send_massmail

            # Patch threads to prevent massmail background threads
            original_thread_init = threading.Thread.__init__

            def dummy_thread_init(self, *args, **kwargs):
                original_thread_init(self, *args, **kwargs)
                if hasattr(self, 'run') and self.run.__name__ == 'run':
                    self.run = lambda: None

            threading.Thread.__init__ = dummy_thread_init

        except ImportError:
            pass

