"""
WSGI config for puppet project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os

"""
If you have another location for the config, uncomment the line below and insert a static path to the config file.§
"""
# os.environ['PP_CFG'] = '/etc/panopuppet/config.yaml'


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panopuppet.puppet.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
