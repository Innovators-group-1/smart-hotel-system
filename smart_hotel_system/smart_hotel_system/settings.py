"""
Production settings for smart_hotel_system
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qsl

# ===============================
# BASE DIR
# ===============================
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv()

# ===============================
# SECURITY SETTINGS
# ===============================

# Get from environment variable or use a secure default
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-8i_pw1ass4ikn2zsa*^_7*n+96q2-#h!cp)^flig8ysfu^(n@@')

# Debug mode - should be False in production
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Allowed hosts - set from environment
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Trust proxy headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ===============================
# APPLICATIONS
# ===============================

# Shared apps (available to all tenants and public schema)
SHARED_APPS = [
    'django_tenants',  
    'django_extensions',
    
    # Django built-in apps
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    
    # Your platform admin app (for tenant management)
    'apps.platform_admin_flow',
]

# Tenant-specific apps (isolated per tenant)
TENANT_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    
    # Your tenant apps
    'apps.admin_flow',
    'apps.chef_flow',
    'apps.client_flow',
    'apps.common_flow',
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

# ===============================
# MIDDLEWARE
# ===============================

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # Must be first
    
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ===============================
# URL CONFIGURATION
# ===============================

# Public schema uses this URL config (for tenant creation, health checks, etc.)
PUBLIC_SCHEMA_URLCONF = 'smart_hotel_system.public_urls'

# Tenant schemas use this URL config
ROOT_URLCONF = 'smart_hotel_system.urls'

# ===============================
# TEMPLATES
# ===============================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
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

# ===============================
# DATABASE CONFIGURATION
# ===============================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Detect if using Cloud SQL Unix socket or regular TCP connection
if '/cloudsql/' in DATABASE_URL:
    # Cloud SQL Unix socket connection
    # Format: postgresql://user:password@/dbname?host=/cloudsql/project:region:instance
    tmpPostgres = urlparse(DATABASE_URL)
    
    # Extract query params to get the socket host
    query_params = dict(parse_qsl(tmpPostgres.query))
    socket_path = query_params.get('host', '')
    
    DATABASES = {
        'default': {
            'ENGINE': 'django_tenants.postgresql_backend',
            'NAME': tmpPostgres.path.replace('/', ''),
            'USER': tmpPostgres.username,
            'PASSWORD': tmpPostgres.password,
            'HOST': socket_path,   # Unix socket path
            'PORT': '',            # No port for Unix socket
            'OPTIONS': {
                # No sslmode for Unix socket
                'connect_timeout': 10,
            },
            'CONN_MAX_AGE': 0,
            'CONN_HEALTH_CHECKS': True,
            'DISABLE_SERVER_SIDE_CURSORS': True,
        }
    }

# Database router for django-tenants
DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

# Tenant models
TENANT_MODEL = "platform_admin_flow.HotelTenant"
TENANT_DOMAIN_MODEL = "platform_admin_flow.HotelDomain"

# ===============================
# STATIC FILES
# ===============================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# WhiteNoise configuration for serving static files
# Using CompressedStaticFilesStorage (simpler, doesn't require manifest)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# ===============================
# MEDIA FILES
# ===============================
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = 'quickdine-media'
# Disable querystring authentication for public files (if using publicRead ACL)
GS_QUERYSTRING_AUTH = False
 
MEDIA_URL = f'https://storage.googleapis.com/quickdine-media/'
MEDIA_ROOT = ''

# ===============================
# WSGI/ASGI
# ===============================

WSGI_APPLICATION = 'smart_hotel_system.wsgi.application'
ASGI_APPLICATION = 'smart_hotel_system.asgi.application'

# ===============================
# PASSWORD VALIDATION
# ===============================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ===============================
# INTERNATIONALIZATION
# ===============================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ===============================
# DEFAULT AUTO FIELD
# ===============================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===============================
# LOGGING CONFIGURATION
# ===============================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR', 
            'propagate': False,
        },
    },
}