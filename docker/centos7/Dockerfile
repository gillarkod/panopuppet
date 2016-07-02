FROM centos:7
MAINTAINER propyless at github dot com
#
LABEL "com.example.vendor" = "propyless at github dot com"
LABEL version="v1.4.0"
LABEL description="PanoPuppet v1.4.0 on CentOS 7."
#
# Enable the proxy encv vars if you are behind a firewall, etc
# or use these build-arg options when building the container;
# docker build -t panopuppet:v1.4.0 --build-arg http_proxy=http://proxy.company.co.uk:8080 --build-arg https_proxy=https://proxy.company.co.uk:8080 .
#ENV http_proxy http://proxy.company.co.uk:8080
#ENV https_proxy https://proxy.company.co.uk:8080
#
# Install packages, download PanoPuppet and perform setup.py
RUN yum install -y \
      https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
      https://dl.iuscommunity.org/pub/ius/stable/CentOS/7/x86_64/ius-release-1.0-14.ius.centos7.noarch.rpm && \
    yum install -y \
      python35u \
      python35u-devel \
      python35u-mod_wsgi \
      python35u-pip \
      httpd \
      httpd-devel \
      cyrus-sasl-devel \
      gcc \
      make \
      openldap-devel \
      libyaml-devel && \
    mkdir -p /var/www/panopuppet/staticfiles && \
    curl -L https://github.com/propyless/panopuppet/archive/v1.4.0.tar.gz | tar -xzv -C /tmp  && \
    cd /tmp/panopuppet-1.4.0 && \ 
    python3.5 setup.py install
# Copy local panopuppet.conf and config.yaml
# panopuppet.conf beware of Apache 2.2 settings and not 2.4
COPY panopuppet.conf /etc/httpd/conf.d/
COPY config.yaml /var/www/panopuppet/
# Save on user actions for manage.py and wsgi.py, as they are custom for this container
#COPY manage.py /var/www/panopuppet/
#COPY wsgi.py /var/www/panopuppet/
#
# Perform configuration of PanoPuppet
RUN echo $'#!/usr/bin/python3.5\n\
import os\n\
import sys\n\
\n\
os.environ[\'PP_CFG\'] = \'/var/www/panopuppet/config.yaml\'\n\
\n\
if __name__ == "__main__":\n\
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panopuppet.puppet.settings")\n\
    from django.core.management import execute_from_command_line\n\
    execute_from_command_line(sys.argv)'\
> /var/www/panopuppet/manage.py && \
    echo $'"""\n\
WSGI config for puppet project.\n\
It exposes the WSGI callable as a module-level variable named ``application``.\n\
For more information on this file, see\n\
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/\n\
"""\n\
\n\
import os\n\
\n\
"""\n\
If you have another location for the config, uncomment the line below and insert a static path to the config file.\n\
"""\n\
os.environ[\'PP_CFG\'] = \'/var/www/panopuppet/config.yaml\'\n\
\n\
\n\
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panopuppet.puppet.settings")\n\
from django.core.wsgi import get_wsgi_application\n\
\n\
application = get_wsgi_application()'\
> /var/www/panopuppet/wsgi.py && \
     cd /var/www/panopuppet && \
     echo yes | python3.5 manage.py collectstatic && \
     python3.5 manage.py makemigrations && \
     python3.5 manage.py migrate && \
     chown -R apache:apache /var/www/panopuppet
# Export port 80 for Apache
EXPOSE 80
# Start Apache in foreground
ENTRYPOINT ["apachectl", "-D", "FOREGROUND"]
