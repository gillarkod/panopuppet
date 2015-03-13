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

This code is quite slow, but this is largely due to the amount of data that
needs to be processed. I was considering using celery to distribute queries
and queries to one or more workers but realized that the main issue here is
the amount of time it takes to poll puppetdb of certain things.

You can see here with this profiling output:

<pre>
request start
2015-03-10 10:36:39.796807

jobs start
2015-03-10 10:36:39.801722

population:
time: (0.0, 0.080793)

nodes:
time: (0.0, 0.087991)

event-counts:
time: (0.0, 0.107203)

all_nodes:
time: (0.0, 0.293851)

tot_resource:
time: (0.0, 0.373909)

avg_resource:
time: (0.0, 0.381993)

end jobs
2015-03-10 10:36:40.184869

node statistics start
2015-03-10 10:36:40.184949
2015-03-10 10:36:40.185408
end node statistics

node unreported start
2015-03-10 10:36:40.185437
2015-03-10 10:36:40.308031
end node unreported

generate new dict
2015-03-10 10:36:40.308095
2015-03-10 10:36:40.309542
end generate new dict

end requests
2015-03-10 10:36:40.309616
</pre>

The longest amount of time was actually retrieving information from puppetdb about the 
nodes,average/tot resouces etc.
This part took between 600-900 ms depending on the current load on postgresqldb.

I decided therefore to do some old school caching.
Each request is cached for 60 seconds. This should work quite well with cronjob scheduled puppet
runs since they run at even intervals.


<pre>
Panopuppet without caching:
1000 Clients
1.3 requests/second
64 seconds average response time
</pre>
<pre>
Panopuppet with Caching:
1000 Clients
282.2 requests/second
1.6 seconds average response time
</pre>

Another way to go is by doing a ton of client side calls to puppetdb API.
Talking directly to the puppetdb postgresql server

#### Thanks go to...

* [pypuppetdb](https://github.com/puppet-community/pypuppetdb)

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
 * GCC not compiling... Follow instructions here... http://bugs.python.org/issue21121


### Installation
I have yet to write proper instructions for installing this mod_wsgi or mod_uwsgi.
This is something that will come...

The master branch has a release which includes:
* ldap authentication
* caching

Upcoming branches:
* no_auth
** There will be no ldap authentication support included.

#### Getting Started
manage.py migrate

#### Development Server - Django runserver...

#### Apache

apache + mod_wsgi is recommended for django in production.