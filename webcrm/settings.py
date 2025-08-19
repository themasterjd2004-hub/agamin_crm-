# webcrm/settings.py
import sys
from pathlib import Path
from datetime import datetime as dt
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ImproperlyConfigured

# ---- Django project base ---- #
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'j1c=6$s-dh#$ywt@(q4cm=j&0c*!0x!e-qm6k1%yoliec(15tn)'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ---- Import app-specific settings (if needed) ---- #
try:
    from crm.settings import *  # NOQA
    from common.settings import *  # NOQA
    from tasks.settings import *  # NOQA
    from voip.settings import *  # NOQA
    from .datetime_settings import *  # NOQA
except ImportError:
    pass

# ---- Database ---- #
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "webcrm_db",
        "USER": "crm_user",
        "PASSWORD": "Dhruva123#",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='ONLY_FULL_GROUP_BY', time_zone='+00:00'",
        },
    }
}

# ---- Email ---- #
EMAIL_HOST = '<specify host>'
EMAIL_HOST_USER = 'crm@example.com'
EMAIL_HOST_PASSWORD = '<specify password>'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = 'CRM: '
SERVER_EMAIL = 'test@example.com'
DEFAULT_FROM_EMAIL = 'test@example.com'
ADMINS = [("<Admin1>", "<admin1_box@example.com>")]

# ---- Security / Debug ---- #
DEBUG = True
FORMS_URLFIELD_ASSUME_HTTPS = True

# ---- Internationalization ---- #
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('ar','Arabic'), ('cs','Czech'), ('de','German'), ('el','Greek'),
    ('en','English'), ('es','Spanish'), ('fr','French'), ('he','Hebrew'),
    ('hi','Hindi'), ('id','Indonesian'), ('it','Italian'), ('ja','Japanese'),
    ('ko','Korean'), ('nl','Nederlands'), ('pl','Polish'), ('pt-br','Portuguese'),
    ('ro','Romanian'), ('ru','Russian'), ('tr','Turkish'), ('uk','Ukrainian'),
    ('vi','Vietnamese'), ('zh-hans','Chinese')
]
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / 'locale']

LOGIN_URL = '/admin/login/'

# ---- Applications ---- #
INSTALLED_APPS = [
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crm.apps.CrmConfig',
    'massmail.apps.MassmailConfig',
    'analytics.apps.AnalyticsConfig',
    'help',
    'tasks.apps.TasksConfig',
    'chat.apps.ChatConfig',
    'voip',
    'common.apps.CommonConfig',
    'settings'
]

# ---- Middleware ---- #
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.utils.usermiddleware.UserMiddleware'
]

ROOT_URLCONF = 'webcrm.urls'

# ---- Templates ---- #
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
            ],
        },
    },
]

WSGI_APPLICATION = 'webcrm.wsgi.application'

# ---- Password validation ---- #
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---- Static / Media files ---- #
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "compiled_static"
if STATICFILES_DIRS and STATIC_ROOT in STATICFILES_DIRS:
    raise ImproperlyConfigured("STATIC_ROOT cannot be inside STATICFILES_DIRS")

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

FIXTURE_DIRS = ['tests/fixtures']
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
SITE_ID = 1

# ---- Security Headers ---- #
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_PRELOAD = False
X_FRAME_OPTIONS = "SAMEORIGIN"
DJANGO_RUNSERVER_HIDE_WARNING = True

# ---- CRM-specific settings ---- #
SECRET_CRM_PREFIX = '123'
SECRET_ADMIN_PREFIX = '456-admin'
SECRET_LOGIN_PREFIX = '789-login'
CRM_IP = "127.0.0.1"
CRM_REPLY_TO = ["'Do not reply' <crm@example.com>"]
NOT_ALLOWED_EMAILS = []

APP_ON_INDEX_PAGE = ['tasks', 'crm', 'analytics', 'massmail', 'common', 'settings']
MODEL_ON_INDEX_PAGE = {
    'tasks': {'app_model_list': ['Task','Memo']},
    'crm': {'app_model_list': ['Request','Deal','Lead','Company','CrmEmail','Payment','Shipment']},
    'analytics': {'app_model_list': ['IncomeStat','RequestStat']},
    'massmail': {'app_model_list': ['MailingOut','EmlMessage']},
    'common': {'app_model_list': ['UserProfile','Reminder']},
    'settings': {'app_model_list': ['PublicEmailDomain','StopPhrase']}
}

VAT = 0
MARK_PAYMENTS_THROUGH_REP = False
SHOW_USER_CURRENT_TIME_ZONE = False
LOAD_EXCHANGE_RATE = False
LOADING_EXCHANGE_RATE_TIME = "6:30"
LOAD_RATE_BACKEND = ""
SITE_TITLE = 'CRM'
ADMIN_HEADER = "ADMIN"
ADMIN_TITLE = "CRM Admin"
INDEX_TITLE = _('Main Menu')
MAILING = True
COPYRIGHT_STRING = f"Django-CRM. Copyright (c) {dt.now().year}"
PROJECT_NAME = "Django-CRM"
PROJECT_SITE = "https://github.com/DjangoCRM/django-crm/"

# CRM flags needed for tests/admin
SHIPMENT_DATE_CHECK = True
KEEP_TICKET = True

# ---- Testing adjustments ---- #
TESTING = sys.argv[1:2] == ['test']
if TESTING:
    SECURE_SSL_REDIRECT = False
    LANGUAGE_CODE = 'en'
    LANGUAGES = [('en',''),('uk','')]
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    IMAP_CONNECTION_IDLE = 0
    REUSE_IMAP_CONNECTION = False
