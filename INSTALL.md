Installation processes for different distributions are found here.

* **Current Guides**
  * RHEL
    * [RHEL/CentOS 7 (with setup.py)](#rhelcentos-7-with-setuppy)
    * [RHEL/CentOS 7 (without setup.py - includes instructions for SELinux contexts)](#rhelcentos-7-without-setuppy---includes-instructions-for-selinux-contexts)
  * Ubuntu/Debian
    * [Debian/Jessie](#debianjessie)

* **Deprecated Guides**
  * RHEL
    * [RHEL/CentOS 6](#rhelcentos-6)

# RHEL/CentOS

## RHEL/CentOS 7 (with setup.py)

_This guide uses @sheijmans guide for RHEL/CentOS7 as a base but has been modified to install panopuppet the new way. So thank you for contributing with your fantastic guide!_

**Preparation**
```
$ sudo yum install git vim wget
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
Add rh-python34 to HTTPD24_HTTPD_SCLS_ENABLED.
**Contents;**
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
7) Create files and folder for static files, wsgi.py, manage.py and config.yaml
```
$ sudo mkdir /opt/rh/httpd24/root/var/www/pp.your.domain.com
$ cd /opt/rh/httpd24/root/var/www/pp.your.domain.com
$ sudo touch config.yaml manage.py wsgi.py
```

8) Populate the PanoPuppet configuration and make sure that it will work for your PuppetDB Environment.
Important configuration that you need to set.
The rest you will have to work out yourself (PuppetDB, Run Time, SSL Certificates etc..)
```
$ sudo vim config.yaml
```
**Contents;**
```
SQLITE_DIR: '/opt/rh/httpd24/root/var/www/pp.your.domain.com'
SECRET_KEY: <CHANGE TO SOMETHING ELSE>
DEBUG: false
TEMPLATE_DEBUG: false
ALLOWED_HOSTS:
  - '*' # Allow all to access basically
LANGUAGE_CODE: <your lang code>
TIME_ZONE: <Your preferred timezone>
STATIC_ROOT: '/opt/rh/httpd24/root/var/www/pp.your.domain.com/staticfiles'
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
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os

"""
If you have another location for the config, uncomment the line below and insert a static path to the config file.
"""
os.environ['PP_CFG'] = '/opt/rh/httpd24/root/var/www/pp.your.domain.com/config.yaml'


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panopuppet.puppet.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

10) Populate manage.py and collect staticfiles, populate database, create super user.
```
$ sudo vim manage.py
```
**Contents;**
```
#!/usr/bin/env python
import os
import sys

os.environ['PP_CFG'] = '/opt/rh/httpd24/root/var/www/pp.your.domain.com/config.yaml'

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panopuppet.puppet.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
```
We can now collect the staticfiles required for panopuppet and django admin pages.
The reason we do this manually is so that all the css files for both panopuppet and the django admin pages are present in the same directory.
```
$ sudo python manage.py collectstatic
```
**When running the above command you should see a statement confirming the location of where the staticfiles will be placed. If all is configured correct in `config.yaml` you should get this path: `/opt/rh/httpd24/root/var/www/pp.your.domain.com/staticfiles`**

Create the migrations.
```
$ sudo python manage.py makemigrations
```
Create the database and also make a superuser accounts
```
$ sudo python manage.py syncdb
```

11)
Set the correct owner and perms to the _/opt/rh/httpd24/root/var/www/pp.your.domain.com_ folder
```
$ sudo chown -R apache:apache /opt/rh/httpd24/root/var/www/pp.your.domain.com
```

12) Restart httpd24-httpd service and it should work.
```
$ sudo systemctl restart httpd24-httpd
```

## RHEL/CentOS 7 (without setup.py - includes instructions for SELinux contexts)
This installation "guide" assumes that panopuppet has been extracted to /srv/repo
```
$ sudo yum install git
$ sudo mkdir -p /srv/repo
$ sudo chown -R `whoami`  /srv
$ cd /srv/repo
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
$ sudo yum install wget
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
Contents;
```
LoadModule wsgi_module modules/mod_wsgi.so
```

5) Create a virtualenv instance for panopuppet.
```
$ sudo mkdir /srv/.virtualenvs
$ sudo chown `whoami`  /srv/.virtualenvs
$ cd /srv/.virtualenvs
$ virtualenv panopuppet
$ cd panopuppet/
$ source bin/activate
```

6) Install the python modules needed for panopuppet to function.
```
$ cd /srv/repo/panopuppet
$ pip install -r requirements.txt
```

7) Create Panopuppet config for httpd24.
```
sudo vim /opt/rh/httpd24/root/etc/httpd/conf.d/panopuppet.conf
```
Contents;
```
WSGISocketPrefix /var/run/wsgi
<VirtualHost *:80>
    ServerName pp.your.domain.com
    WSGIDaemonProcess panopuppet user=apache group=apache threads=5 python-path=/srv/repo/panopuppet:/srv/.virtualenvs/panopuppet/lib/python3.4/site-packages
    WSGIScriptAlias / /srv/repo/panopuppet/panopuppet/puppet/wsgi.py
    ErrorLog /var/log/httpd24/panopuppet.error.log
    CustomLog /var/log/httpd24/panopuppet.access.log combined

    Alias /static /srv/staticfiles/
    <Directory /srv/staticfiles>
	    Require all granted
    </Directory>

    <Directory /srv/repo/panopuppet>
        Require all granted
    </Directory>

    <Directory /srv/repo/panopuppet/>
        WSGIProcessGroup panopuppet
    </Directory>
</VirtualHost>
```

8) Create and configure PanoPuppet config.yaml file.
```
$ cp /srv/repo/panopuppet/config.yaml.example /srv/repo/panopuppet/config.yaml
```
Use your favourite text editor to modify the file with the correct values for your envionrment.
Please note that the example configuration file contains an example for puppetdb connection with and without SSL.

Depending on your puppet infrastructure you may or may not need to specify certificate, private key and cacert files to authenticate
with puppetdb, puppetmaster filebucket and fileserver.

9) Create PanoPuppet manage.py and populate the /srv/staticfiles directory with the staticfiles.
```
$ sudo mkdir /srv/staticfiles
$ sudo chown `whoami` /srv/staticfiles
$ cd /srv/repo/panopuppet
$ vim manage.py
```
Contents;
```
#!/usr/bin/env python
import os
import sys

os.environ['PP_CFG'] = '/srv/repo/panopuppet/config.yaml'

if __name__ == "__main__":
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panopuppet.puppet.settings")
	from django.core.management import execute_from_command_line
	execute_from_command_line(sys.argv)
```
We can now collect the staticfiles required for panopuppet and django admin pages.
```
$ python manage.py collectstatic
```
Say 'yes' to the question it might ask about overwriting files in the /srv/collectstatic folder.

10) Populate the django database so that users logging in with LDAP or local users are populated into django.
```
$ python manage.py makemigrations
$ python manage.py migrate
```

11) OPTIONAL STEP IF YOU DON'T WANT TO USE LDAP AND YOU ARE JUST TESTING.
Create a local superuser to log in as
```
$ python manage.py createsuperuser
```
You are able to create some other users in the admin page located at http://pp.your.domain.com/puppetadmin

12) chown the /srv/repo/panopuppet directory recursively to the http user you want running panopuppet.
This is to make sure that the panopuppet application can access the local database containing users etc.
Support for other databases will be added at a later time.
Make sure to replace 'apache' with the appropriate user and group.
```
$ sudo chown -R apache:apache /srv/repo/panopuppet
```

13) Configure SELinux for panopuppet
```
$ sudo setsebool -P httpd_can_network_connect on
$ sudo semanage fcontext -a -t httpd_sys_content_t "/srv/repo/panopuppet/panopuppet(/.*)?"
$ sudo semanage fcontext -a -t httpd_sys_rw_content_t "/srv/repo/panopuppet/panopuppet/pano/views(/.*)?"
$ sudo semanage fcontext -a -t httpd_sys_rw_content_t "/srv/repo/panopuppet/panopuppet/pano/methods(/.*)?"
$ sudo semanage fcontext -a -t httpd_sys_rw_content_t "/srv/repo/panopuppet/panopuppet/pano/puppetdb(/.*)?"
$ sudo semanage fcontext -a -t httpd_sys_rw_content_t "/srv/repo/panopuppet/panopuppet/pano/templatetags(/.*)?"
$ sudo semanage fcontext -a -t httpd_sys_rw_content_t "/srv/repo/panopuppet/panopuppet/pano/__pycache__(/.*)?"
$ sudo semanage fcontext -a -t httpd_sys_rw_content_t "/srv/repo/panopuppet/panopuppet/puppet/__pycache__(/.*)?"
$ sudo semanage fcontext -a -t httpd_sys_content_t "/srv/repo/panopuppet/config.yaml"
$ sudo semanage fcontext -a -t httpd_sys_rw_content_t "/srv/repo/panopuppet"
$ sudo semanage fcontext -a -t httpd_sys_rw_content_t "/srv/repo/panopuppet/panopuppet.db.sqlite3"
$ sudo semanage fcontext -a -t httpd_sys_content_t "/srv/staticfiles(/.*)?"
$ sudo semanage fcontext -a -t bin_t "/srv/.virtualenvs/panopuppet/bin(/.*)?"
$ sudo semanage fcontext -a -t lib_t "/srv/.virtualenvs/panopuppet/lib(/.*)?"
$ sudo restorecon -vFR /srv/
```

14) Restart httpd24-httpd service and it should work.
```
$ sudo systemctl restart httpd24-httpd
```

# Debian/Ubuntu

## Debian/jessie

1) Install Debian packages needed
* apt-get install git gcc make python3 python3-dev cyrus-sasl2-dbg libsasl2-dev virtualenvwrapper python3-arrow python3-requests python3-pip libldap2-dev libyaml libyaml-dev apache2 apache2-dev python-setuptools pyconfigure python-dev libsasl2-dev

2) Setup apache config
* hostname=$(hostname -f)
* cat ->/etc/apache2/sites-available/001-panopuppet.conf <<EOF
```
WSGISocketPrefix /var/run/wsgi
<VirtualHost *:80>
    ServerName $hostname
    WSGIDaemonProcess panopuppet user=www-data group=www-data threads=5 python-path=/opt/panopuppet
    WSGIScriptAlias / /opt/panopuppet/puppet/wsgi.py
    ErrorLog /var/log/apache2/panopuppet.error.log
    CustomLog /var/log/apache2/panopuppet.access.log combined

    Alias /static /srv/staticfiles/
    <Directory /srv/staticfiles/>
        Satisfy Any
        Allow from all
    </Directory>

    <Directory /opt/panopuppet/>
        WSGIProcessGroup panopuppet
        Satisfy Any
        Allow from all
    </Directory>
</VirtualHost>

EOF
```
* a2ensite 001-panopuppet.conf

3) install python modules not available as debian package
* python3 -m pip install Django==1.8.8
* python3 -m pip install django-auth-ldap==1.2.7
* python3 -m pip install pytz
* python3 -m pip install pyyaml

4) Debian package libapache2-mod-wsgi-py3 does not work for panopuppet
* python3 -m pip install mod_wsgi
* /usr/local/bin/mod_wsgi-express install-module
* a2enmod wsgi_express

5) Clone git Repo and edit config file
* cd /opt
* git clone https://github.com/propyless/panopuppet.git
* cd /opt/panopuppet/
* cp config.yaml.example /etc/panopuppet/config.yaml
* vi /etc/panopuppet/config.yaml # set parameters for
```
PUPPETMASTER_CLIENTBUCKET_HOST
PUPPETMASTER_FILESERVER_HOST
ENABLE_PERMISSIONS: false
ALLOWED_HOSTS
TIME_ZONE
```

6) Setup panopuppet files (maybe not needed with version 1.3)
* python3 ./panopuppet/manage.py migrate
* python3 ./panopuppet/manage.py createsuperuser
* python3 ./panopuppet/manage.py makemigrations

7) Ownership must be changed to apache user (maybe not needed with version 1.3)
* chown -R www-data:www-data /opt/panopuppet

8) Set up DB directory
* mkdir /var/www/panopuppet/
* chown www-data:www-data /var/www/panopuppet/

9) Install panopuppet executeables
* python3 ./setup.py build
* python3 ./setup.py install

10) Setup local sqlite DB
* restart apache service and connect to panopuppet webservice => creates /var/www/panopuppet/panopuppet.db.sqlite3
* python3 ./panopuppet/manage.py startproject production
* python3 ./panopuppet/manage.py collectstatic
* python3 ./panopuppet/manage.py syncdb

if you want to add a different user:
* python3 ./panopuppet/manage.py createsuperuser

maybe some old data have to be migrated:
* python3 ./panopuppet/manage.py makemigrations
* python3 ./panopuppet/manage.py migrate

11) start apache service
* service apache2 restart


# Deprecated guides

## RHEL/CentOS 6
This installation "guide" assumes that panopuppet has been extracted to /srv/repo
```
mkdir -p /srv/repo
cd /srv/repo
git clone https://github.com/propyless/panopuppet.git panopuppet
```

1) Add the IUS and EPEL repository
```
$ sudo yum install epel-release
$ sudo yum install http://dl.iuscommunity.org/pub/ius/stable/CentOS/6/x86_64/ius-release-1.0-11.ius.centos6.noarch.rpm
```

2) Now we can install python 3.x and the ldap dependencies for the python-ldap module
```
$ sudo yum install python33 python33-devel openldap-devel cyrus-sasl-devel gcc make
```
Side note: You should install virtualenv if you do not already use it because its fantastic.
```
$ sudo yum install python-virtualenv python-virtualenvwrapper
```

3) Install httpd and mod_wsgi for python33
```
$ sudo yum install httpd python33-mod_wsgi
```

4) We will now if configure virtualenv abit.
I usually add the lines below to my .bashrc file and set some environment variables used for virtualenv.
```
export WORKON_HOME=/srv/.virtualenvs
export PROJECT_HOME=/srv/repo
source /usr/bin/virtualenvwrapper.sh
```
After adding the above lines we need to create the /srv/.virtualenvs directory.
```
$ mkdir /srv/.virtualenvs
```

5) Create a virtualenv instance for panopuppet. (Make sure that you sourced the bashrc file after modifying it)
```
$ which python3
```
This will give us the path to python3 which we installed at step 2.
```
$ mkvirtualenv -p /usr/bin/python3 panopuppet
```
You now have a python virtualenv in /srv/.virtualenvs/panopuppet, if you run the below command you will see that python3 is chosen from the .virtualenv directory.
```
$ which python3
```
If you want to use the system python3 binary again you can run the command
```
$ deactivate
```

6) If you ran the deactivate command, run the below command to activate the virtualenv again.
```
$ workon panopuppet
```

7)We will install the python modules needed for panopuppet to function.
```
$ cd /srv/repo/panopuppet
$ pip install -r requirements.txt
```

8) This directory will be needed to serve the static files.
```
mkdir /srv/staticfiles
```

9) Apache httpd config
```
WSGISocketPrefix /var/run/wsgi
<VirtualHost *:80>
    ServerName pp.your.domain.com
    WSGIDaemonProcess panopuppet user=apache group=apache threads=5 python-path=/srv/repo/panopuppet:/srv/.virtualenvs/panopuppet/lib/python3.3/site-packages
    WSGIScriptAlias / /srv/repo/panopuppet/puppet/wsgi.py
    ErrorLog /var/log/httpd/panopuppet.error.log
    CustomLog /var/log/httpd/panopuppet.access.log combined

    Alias /static /srv/staticfiles/
    <Directory /srv/repo/panopuppet>
        Satisfy Any
        Allow from all
    </Directory>

    <Directory /srv/repo/panopuppet/>
        WSGIProcessGroup panopuppet
    </Directory>
</VirtualHost>
```

10) Configure PanoPuppet
```
$ cp /srv/repo/panopuppet/config.yaml.example /srv/repo/panopuppet/config.yaml
```
Use your favourite text editor to modify the file with the correct values for your envionrment.
Please note that the example configuration file contains an example for puppetdb connection with and without SSL.

Depending on your puppet infrastructure you may or may not need to specify certificate, private key and cacert files to authenticate
with puppetdb, puppetmaster filebucket and fileserver.


11) Populate the /srv/staticfiles with the staticfiles
```
$ cd /srv/repo/panopuppet
$ python manage.py collectstatic
```
Say yes to the question it might ask about overwriting files in the /srv/collectstatic folder.

12) chown the /srv/repo/panopuppet directory recursively to the http user you want running panopuppet.
This is to make sure that the panopuppet application can access the local database containing users etc.
Support for other databases will be added at a later time.
Make sure to replace 'apache' with the appropriate user and group.
```
$ chown -R apache:apache /srv/repo/panopuppet
```

13) Populate the django database so that users logging in with LDAP or local users are populated into django.
```
$ python manage.py makemigrations
$ python manage.py migrate
```

14) OPTIONAL STEP IF YOU DON'T WANT TO USE LDAP AND YOU ARE JUST TESTING.
Create a local superuser to log in as
```
$ python manage.py createsuperuser
```
You are able to create some other users in the admin page located at http://panopuppet.your-domain.com/admin

15) Restart Httpd service and it should work.
```
$ sudo /etc/init.d/httpd restart
```
