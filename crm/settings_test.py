"""
Test settings for running automated tests.
"""

from .settings import *

# Use in-memory SQLite for tests
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
}

# Use in-memory email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable threads for massmail during tests
MASSMAIL_DISABLE_THREADS = True
MIGRATION_MODULES = {'massmail': None}

# Simplify password hashing
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Logging for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
}

# Override static/media for tests
STATIC_ROOT = BASE_DIR / "compiled_static_test"
MEDIA_ROOT = BASE_DIR / "media_test"

# Other overrides
GEOIP = False
OAUTH2_DATA = {}
IMAP_CONNECTION_IDLE = 0
IMAP_NOOP_PERIOD = 0
REUSE_IMAP_CONNECTION = False
