"""
WSGI config for puppet project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os

os.environ['PP_CFG'] = '/var/www/html/panopuppet/config.yaml'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panopuppet.puppet.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
