# PanoPuppet

## Features
* Fast and easy to use
* Uses PuppetDB API to retrieve information
* Filebucket and Fileserver support
* Diff support between old and new file
* Fully featured Dashboard for use with PuppetDB
* Analytics Page providing insight into your puppet environment
* LDAP Authentication
* Events Analyzer (Like Events Inspector from Puppet Enterprise)

## Future plans
* Docker image to quickly install a panopuppet dashboard
* Search nodes by facts and subqueries


### Introduction

PanoPuppet, Panorama Puppet or PP is a web frontend that interfaces with PuppetDB
and gives you a panorama view over your puppet environment(s). Its coded using Python3
using the Django Framework for the web interface and requests library to interface with
puppetDB. It also uses Bootstrap for the CSS and Jquery for some tablesorting.

The interface was written originally as an idea from work, we have tried to
use different types of web interfaces that show the status of the puppet
environment. Most of them were too slow, too bloated to give us the information
we wanted quickly. Why should PuppetDB which has an amazing response time
suffer from a slow frontend. When you reach a point where the environment could
have over 20k puppetized nodes you need something fast.

This was written for a multi-tenant site across several datacenters.

### About the code

I am not a developer really so most of my code could look like it came out of a
rats den. I have followed the PEP8 standards for coding. The comments might be sparse,
sorry for that.

Code has been relatively fixed and optimized even though i'm sure there is much more I can do.

#### Thanks go to...

* [pypuppetdb](https://github.com/puppet-community/pypuppetdb) - Solved some issues which I got stuck at

### Screenshots
![Dashboard](screenshots/pano_dash.png)
![Nodes View](screenshots/pano_nodes.png)
![Reports View](screenshots/pano_reports.png)
![Events View](screenshots/pano_events.png)
![Facts View](screenshots/pano_facts.png)


### Requirements

Requires python3
install requirements listed in requirements.txt
Recommended to use virtualenv (+ virtualenvwrapper)


#### Problems with python-ldap python 3 fork.
I had some issues installing python-ldap using the python3 fork on a RHEL6 server
Here are some of the issues I had...
 * missing dependencies - yum install python-devel openldap-devel cyrus-sasl-devel
 * GCC not compiling the python-ldap module... Follow instructions here... http://bugs.python.org/issue21121


### Installation

#### RHEL/CentOS 6
```
This installation "guide" assumes that panopuppet has been extracted to /srv/repo
mkdir -p /srv/repo
cd /srv/repo
git clone https://github.com/propyless/panopuppet.git panopuppet
```

1. Add the IUS and EPEL repository
```
$ sudo yum install epel-release
$ sudo yum install http://dl.iuscommunity.org/pub/ius/stable/CentOS/6/x86_64/ius-release-1.0-11.ius.centos6.noarch.rpm
```
2. Now we can install python 3.x and the ldap dependencies for the python-ldap module
`$ sudo yum install python33 python33-devel openldap-devel cyrus-sasl-devel gcc make`
```
Side note: You should install virtualenv if you do not already use it because its fantastic.
$ sudo yum install virtualenv virtualenvwrapper
```
3. Install httpd and mod_wsgi for python33
`$ sudo yum install httpd python33-mod_wsgi`
4. We will now if configure virtualenv abit.
```
I usually add the lines below to my .bashrc file and set some environment variables used for virtualenv.
export WORKON_HOME=/srv/.virtualenvs
export PROJECT_HOME=/srv/repo
source /usr/bin/virtualenvwrapper.sh

After adding the above lines we need to create the /srv/.virtualenvs directory.
$ mkdir /srv/.virtualenvs
```
5. Create a virtualenv instance for panopuppet. (Make sure that you sourced the bashrc file after modifying it)
`$ which python3`
This will give us the path to python3 which we installed at step 2.
`$ mkvirtualenv -p /usr/bin/python3 panopuppet`
You now have a python virtualenv in /srv/.virtualenvs/panopuppet, if you run the below command you will see that python3 is chosen from the .virtualenv directory.
`$ which python3`
If you want to use the system python3 binary again you can run the command
`$ deactivate`
6. If you ran the deactivate command, run the below command to activate the virtualenv again.
`workon panopuppet`
7. We will install the python modules needed for panopuppet to function.
```
$ cd /srv/repo/panopuppet
$ pip install -r requirements.txt
```
If you hit any troubles with the python-ldap module you may need to run this command before running the pip install command again.
This work around was taken from: http://bugs.python.org/issue21121
`export CFLAGS=$(python3.3 -c 'import sysconfig; print(sysconfig.get_config_var("CFLAGS").replace("-Werror=declaration-after-statement",""))')`
8. This directory will be needed to serve the static files.
mkdir /srv/staticfiles
9. Apache httpd config
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
10. Populate the /srv/staticfiles with the staticfiles
`$ cd /srv/repo/panopuppet`
`$ python manage.py collectstatic` Say yes to the question it might ask about overwriting files in the /srv/collectstatic folder.

11. Restart Httpd service and it should work.
`/etc/init.d/httpd restart`


### Available branches

The master branch has a release which includes:
* ldap authentication
* caching

Upcoming branches:
* no_auth
  * There will be no ldap authentication support included.

#### Getting Started
manage.py migrate

#### Development Server - Django runserver...

#### Apache

apache + mod_wsgi is recommended for django in production.
