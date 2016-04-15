"""
Django settings for puppet project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

import yaml

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# config_file = os.path.join(BASE_DIR, 'config.yaml')
config_file = '/etc/panopuppet/config.yaml'
with open(config_file, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = cfg.get('SECRET_KEY', None)
if SECRET_KEY is None:
    print('Secret is not specified')
    exit(1)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = cfg.get('DEBUG', True)

ALLOWED_HOSTS = cfg.get('ALLOWED_HOSTS', ['127.0.0.1'])
if type(ALLOWED_HOSTS) != list:
    print('ALLOWED_HOSTS must be specified as an array.')
    exit(1)

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'panopuppet.pano',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # timezone awareness
    'panopuppet.puppet.middlewares.TimezoneMiddleware',
)

ROOT_URLCONF = 'panopuppet.puppet.urls'

WSGI_APPLICATION = 'panopuppet.puppet.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {

    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(cfg.get('SQLITE_DIR'), 'panopuppet.db.sqlite3'),
    }
}

# Authentication
# Ldap authentication
from panopuppet.pano.settings import AUTH_METHOD, LDAP_SERVER, LDAP_BIND_DN, LDAP_BIND_PW, LDAP_ALLOW_GRP, \
    LDAP_USEARCH_PATH, LDAP_GSEARCH_PATH, STAFF_GRP, SUPERUSER_GRP, ACTIVE_GRP

if AUTH_METHOD == 'ldap':
    import ldap
    from django_auth_ldap.config import LDAPSearch, ActiveDirectoryGroupType

    AUTHENTICATION_BACKENDS = (
        'django_auth_ldap.backend.LDAPBackend',
        'django.contrib.auth.backends.ModelBackend',
    )
    AUTH_LDAP_SERVER_URI = LDAP_SERVER
    AUTH_LDAP_BIND_DN = LDAP_BIND_DN
    AUTH_LDAP_BIND_PASSWORD = LDAP_BIND_PW
    AUTH_LDAP_USER_SEARCH = LDAPSearch(LDAP_USEARCH_PATH,
                                       ldap.SCOPE_SUBTREE, "(name=%(user)s)")
    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(LDAP_GSEARCH_PATH,
                                        ldap.SCOPE_SUBTREE, "(objectClass=Group)")
    AUTH_LDAP_GROUP_TYPE = ActiveDirectoryGroupType()

    AUTH_LDAP_USER_FLAGS_BY_GROUP = dict()
    if ACTIVE_GRP:
        AUTH_LDAP_USER_FLAGS_BY_GROUP['is_active'] = ACTIVE_GRP
    if STAFF_GRP:
        AUTH_LDAP_USER_FLAGS_BY_GROUP['is_staff'] = STAFF_GRP
    if SUPERUSER_GRP:
        AUTH_LDAP_USER_FLAGS_BY_GROUP['is_superuser'] = SUPERUSER_GRP

    AUTH_LDAP_CACHE_GROUPS = True
    AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600
    AUTH_LDAP_REQUIRE_GROUP = LDAP_ALLOW_GRP
    # The following OPT_REFERRALS option is CRUCIAL for getting this
    # working with MS Active Directory it seems, unfortunately I have
    # no idea why; it just hangs if you don't set it to 0 for us.
    AUTH_LDAP_CONNECTION_OPTIONS = {
        ldap.OPT_DEBUG_LEVEL: 0,
        ldap.OPT_REFERRALS: 0,
    }
    AUTH_LDAP_USER_ATTR_MAP = {
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail"
    }
    LOGIN_URL = '/pano/login/'

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'mail_admins': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler'
            },
            'stream_to_console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler'
            },
        },
        'loggers': {
            'django.request': {
                'handlers': ['mail_admins'],
                'level': 'ERROR',
                'propagate': True,
            },
            'django_auth_ldap': {
                'handlers': ['stream_to_console'],
                'level': 'DEBUG',
                'propagate': True,
            },
        }
    }
else:  # or otherwise known as 'basic' auth
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
    )
    LOGIN_URL = '/pano/login/'

# Expire sessions at browser close
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# Expire Session after x hours
SESSION_AGE = cfg.get('SESSION_AGE', 60)
SESSION_COOKIE_AGE = SESSION_AGE * 3600


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = cfg.get('LANGUAGE_CODE', 'sv-SE')
TIME_ZONE = cfg.get('TIME_ZONE', 'Europe/Stockholm')
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = cfg.get('STATIC_ROOT', '/usr/share/panopuppet/static/')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': '/path/to/my/templates',
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.core.context_processors.debug",
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.core.context_processors.static",
                "django.contrib.messages.context_processors.messages",
                "django.core.context_processors.request",
            ],
            'debug': cfg.get('TEMPLATE_DEBUG', True),
        }
    }
]
