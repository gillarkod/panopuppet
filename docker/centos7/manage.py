#!/usr/bin/python3.5
import os
import sys

os.environ['PP_CFG'] = '/var/www/panopuppet/config.yaml'

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panopuppet.puppet.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
