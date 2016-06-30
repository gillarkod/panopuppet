FROM centos:6
MAINTAINER Alastair Munro: spicysomtam at github dot com
#
LABEL "com.example.vendor" = "propyless at github dot com"
LABEL version="v0.x"
LABEL description="panopuppet v0.x on centos6. Follows the authors install instructions for best compatibility."
#
# Enable the proxy encv vars if you are behind a firewall, etc
ENV http_proxy http://proxy.company.co.uk:8080
ENV https_proxy https://proxy.company.co.uk:8080
RUN yum install -y \
      https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm \
      http://dl.iuscommunity.org/pub/ius/stable/CentOS/6/x86_64/ius-release-1.0-11.ius.centos6.noarch.rpm && \
    yum install -y \
      cyrus-sasl-devel \
      gcc \
      git \
      httpd \
      make \
      openldap-devel \
      python33 \
      python33-devel \
      python33-mod_wsgi \
      python-virtualenv \
      python-virtualenvwrapper && \
    mkdir -p /srv/repo /srv/.virtualenvs && \
    cd /srv/repo && \
    git clone -b v0.x https://github.com/propyless/panopuppet.git panopuppet && \
    echo "export WORKON_HOME=/srv/.virtualenvs" >> /root/.bashrc && \
    echo "export PROJECT_HOME=/srv/repo" >> /root/.bashrc && \
    echo "source /usr/bin/virtualenvwrapper.sh" >> /root/.bashrc && \
    source  /root/.bashrc && \
    mkvirtualenv -p /usr/bin/python3 panopuppet
COPY panopuppet.conf /etc/httpd/conf.d/
COPY config.yaml /srv/repo/panopuppet/
#
# Added a hack for the ldap search filter for settings.py
RUN source  /root/.bashrc && \
    workon panopuppet && \
    cd /srv/repo/panopuppet && \
    pip install -r requirements.txt && \
    echo yes|python manage.py collectstatic && \
    python manage.py makemigrations && \
    python manage.py migrate && \
    sed -i 's/name=/sAMAccountName=/' puppet/settings.py && \
    chown -R apache:apache /srv/repo/panopuppet && \
    echo "OPTIONS='-D FOREGROUND'" >> /etc/sysconfig/httpd
EXPOSE 80
# Since we set the options above the service run below will be in foreground and block.
# I could not get this app working running with only the apache binary; seems to need
# to be in the service wrapper. Needs more debugging, but time is a limited resource!
CMD service httpd start
