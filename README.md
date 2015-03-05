# PanoPuppet


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

I am not a developer, most of my code could look like it came out of a
rats den. I have followed the PEP8 standards for coding. The comments might be sparse,
sorry for that.
I may also have taken bits of code from other PuppetDB dashboards. Mostly because
they have solved a problem and I did not feel like reinventing the wheel.

#### Thanks go to...

* [pypuppetdb](https://github.com/puppet-community/pypuppetdb)

### Screenshots
![Dashboard](screenshots/pano_dash.png)
![Nodes View](screenshots/pano_nodes.png)
![Reports View](screenshots/pano_reports.png)
![Events View](screenshots/pano_events.png)
![Facts View](screenshots/pano_facts.png)


Requires python3
install requirements listed in requirements.txt
Recommended to use virtualenv (+ virtualenvwrapper)

manage.py migrate

apache + mod_wsgi is recommended for django in production

