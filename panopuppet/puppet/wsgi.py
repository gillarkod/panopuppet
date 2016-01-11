"""
WSGI config for puppet project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
import sys
from puppet.settings import BASE_DIR

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "puppet.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
