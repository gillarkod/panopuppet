Installation processes for different distributions are found here.

* **Current Guides**
  * RHEL
    * [RHEL/CentOS 7 (with setup.py)](#rhelcentos-7-with-setuppy)
    * [RHEL/CentOS 7 (without setup.py - Includes instructions for SELinux contexts](#rhelcentos-7)
  * Ubuntu/Debian
    * [Debian/Jessie](#debianjessie)

* **Deprecated Guides**
  * RHEL
    * [RHEL/CentOS 6](#rhelcentos-6)

# RHEL/CentOS

## RHEL/CentOS 7 (With setup.py)

_This guide uses @sheijmans guide for RHEL/CentOS7 as a base but has been modified to install panopuppet the new way. So thank you for contributing with your fantastic guide!_

**Preparation**
```
$ sudo yum install git vim wget
$ sudo mkdir -p /srv/repo
$ sudo chown -R <user> /srv
$ cd /tmp
$ git clone https://github.com/propyless/panopuppet.git panopuppet
```

1) Install the Software Collections repositories for rh-pyhton34 and httpd24.
```
$ sudo yum install scl-utils
$ sudo yum install https://www.softwarecollections.org/en/scls/rhscl/rh-python34/epel-7-x86_64/download/rhscl-rh-python34-epel-7-x86_64.noarch.rpm
$ sudo yum install https://www.softwarecollections.org/en/scls/rhscl/httpd24/epel-7-x86_64/download/rhscl-httpd24-epel-7-x86_64.noarch.rpm
```

2) Install rh-python34 and the dependencies for the python-ldap module.
```
$ sudo yum install rh-python34 libyaml-devel openldap-devel cyrus-sasl-devel gcc make
```

3) Install httpd24.
```
$ sudo yum install httpd24 httpd24-httpd-devel
```
Enable rh-python34 in httpd24;
```
$ sudo vim /opt/rh/httpd24/service-environment
```
Add rh-python34 to HTTPD24_HTTPD_SCLS_ENABLED;
```
HTTPD24_HTTPD_SCLS_ENABLED="httpd24 rh-python34"
```
Enable/start httpd24-httpd service;
```
$ sudo systemctl enable httpd24-httpd
$ sudo systemctl start httpd24-httpd
$ sudo systemctl status httpd24-httpd
```
Configure firewall for httpd24;
```
$ sudo firewall-cmd --permanent --add-service=http
$ sudo firewall-cmd --add-service=http
```

4) Compile mod_wsgi for rh-python34.
rh-python34-mod_wsgi contains a 'bug' which will segfault panopuppet, that's why we compile the latest version.
```
$ cd
$ scl enable rh-python34 bash
$ scl enable httpd24 bash
$ wget https://pypi.python.org/packages/source/m/mod_wsgi/mod_wsgi-4.4.21.tar.gz
$ tar -xzvf mod_wsgi-4.4.21.tar.gz
$ cd mod_wsgi-4.4.21
```
Determine location of rh-pyhton34 version;
```
$ which python
```
Use this location in the configure of mod_wsgi;
```
$ ./configure --with-python=/opt/rh/rh-python34/root/usr/bin/python
$ make
$ sudo make install
```
Configure mod_wsgi module for httpd24;
```
$ sudo vim /opt/rh/httpd24/root/etc/httpd/conf.modules.d/10-mod_wsgi-4421.conf
```
**Contents;**
```
LoadModule wsgi_module modules/mod_wsgi.so
```

5) Install the python modules needed for panopuppet to function.
```
$ cd /tmp/panopuppet
$ python setup.py install
```
6) Create Panopuppet config for httpd24.
```
$ sudo vim /opt/rh/httpd24/root/etc/httpd/conf.d/panopuppet.conf
```
**Contents;**
```
WSGISocketPrefix /var/run/wsgi
<VirtualHost *:80>
    ServerName pp.your.domain.com
    WSGIDaemonProcess panopuppet user=apache group=apache threads=5 python-path=/opt/rh/rh-python34/root/usr/lib/python3.4/site-packages
    WSGIScriptAlias / /opt/rh/httpd24/root/var/www/pp.your.domain.com/wsgi.py
    ErrorLog /var/log/httpd24/panopuppet.error.log
    CustomLog /var/log/httpd24/panopuppet.access.log combined

    Alias /static /opt/rh/httpd24/root/var/www/pp.your.domain.com/staticfiles

    <Directory /opt/rh/httpd24/root/var/www/pp.your.domain.com/staticfiles>
        Require all granted
    </Directory>

    <Directory /opt/rh/rh-python34/root/usr/lib/python3.4/site-packages/panopuppet-1.3-py3.4.egg>
        WSGIProcessGroup panopuppet
        Require all granted
    </Directory>
</VirtualHost>
```
7) Create folders for static files, wsgi.py, manage.py, config.yaml
```
$ sudo mkdir /opt/rh/httpd24/root/var/www/pp.your.domain.com
$ cd /opt/rh/httpd24/root/var/www/pp.your.domain.com
$ sudo touch config.yaml manage.py wsgi.py
```

8) Populate the PanoPuppet configuration and make sure that it will work for your PuppetDB Environment.
Important configuration that you need to set. The rest you will have to work out yourself (PuppetDB, Run Time, SSL Certificates etc..)
```
SQLITE_DIR: '/opt/rh/httpd24/root/var/www/pp.your.domain.com/'
SECRET_KEY: <CHANGE TO SOMETHING ELSE>
DEBUG: false
TEMPLATE_DEBUG: false
ALLOWED_HOSTS:
  - '*' # Allow all to access basically
LANGUAGE_CODE: <your lang code>
TIME_ZONE: <Your preferred timezone>
STATIC_ROOT: '/opt/rh/httpd24/root/var/www/pp.takeshi.se/staticfiles'
```

9) Populate wsgi.py and configure it with the location for the PanoPuppet configuration file.
_I will assume that you are still in the folder we changed our cwd to in step 8._
```
$ sudo vim wsgi.py
```
**Contents;**
```
"""
WSGI config for puppet project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployme