import os

from django.utils.translation import gettext_lazy as _

from . import INSTALLED_APPS

SITE_ID = 1

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media_root')
STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')

BOWER_COMPONENTS_ROOT = os.path.join(BASE_DIR, 'components_root')

FIXTURE_DIRS = (
   os.path.join(BASE_DIR, 'fixtures'),
)

INSTALLED_APPS += [
    'allauth',
    'allauth.account'
]

ACCOUNT = True
ACCOUNT_SIGNUP = True
SOCIALACCOUNT = False

PROJECT_SEND_ISSUE = True

PROJECT_SEND_INVITE = True

EMAIL_RECIPIENTS_CHOICES = [
    ('email@example.com', 'Emmi Email <email@example.com>'),
]
EMAIL_RECIPIENTS_INPUT = True

SERVICE_PROVIDERS = [
    ('github', _('GitHub'), 'rdmo.services.providers.GitHubProvider')
]

GITHUB_PROVIDER = {
    'client_id': '',
    'client_secret': ''
}

'''
LOGGING
'''
LOGGING_DIR = os.path.join(BASE_DIR, 'log')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        }
    },
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s: %(message)s'
        },
        'name': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
        },
        'console': {
            'format': '[%(asctime)s] %(message)s'
        },
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(filename)s %(lineno)d: %(message)s',
            'datefmt': '%H:%M:%S'
        },
        'fullverbose': {
            'format': '%(asctime)s [%(levelname)s] %(pathname)s %(lineno)d: %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'error_log': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'rdmo_error.log'),
            'formatter': 'default'
        },
        'rdmo_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'rdmo.log'),
            'formatter': 'fullverbose'
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins', 'error_log'],
            'level': 'ERROR',
            'propagate': True
        },
        'rdmo': {
            'handlers': ['rdmo_log'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
