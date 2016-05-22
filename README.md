# PanoPuppet

[![Join the chat at https://gitter.im/propyless/panopuppet](https://badges.gitter.im/propyless/panopuppet.svg)](https://gitter.im/propyless/panopuppet?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

PanoPuppet is a PuppetDB dashboard, it uses the information available
in PuppetDB and visualizes it for you with lists and graphs.
You are able to browse through the latest changes in reports, nodes, resources,
classes and types. Many features were features requested by my colleagues.

Its written and designed with an enterprise companies needs as a focus point.
Where there are many XFT's and where there may be a need for extra security to
limit the nodes a certain XFT/group should be allowed access too.

For the feature list click here:  [Features](#features)

# Support
* PanoPuppet Releases >= 1.0.0 - Requires PuppetDB == 3.x (Uses the v4 api endpoint)
* PanoPuppet Releases < 1.0.0 - Requires PuppetDB == 2.x (Uses the experimental v4 api endpoint)

To download a specific release you can find them [Here](https://github.com/propyless/panopuppet/releases)

## Use Case
One large company, several hundred XFT's operating from multiples regions.
Security concious company where you may not always want the information available
in PuppetDB available to everyone. Difficult to lock down a ldap/AD group to a
subset of users in PuppetDB alone..

PanoPuppet gives you the ability to create PuppetDB Queries with a easy to use tool
and use those rules to lock down an active directory group to one or more PuppetDB Queries.

Users that have a rule will then only be able to see nodes that match the rule you created.

PanoPuppet enables you to control and delegate the information in PuppetDB to the users
who need it.

![PanoPuppet Design](screenshots/pp_workflow.png)

# Some random info and tips...
Since this django app can use LDAP/AD Authentication it can be a bit tricky
to get it working for all Actice Directory designs. The default config works
for the environment I tested it with. I have had other users reporting that
they had to change the ldap code to accept nested groups for example or use
another attr for the login name.
If you need help to get it working you are most welcome to create a support issue
in GitHub.

There is an example configuration for you to look at.
I'd suggest you make a copy and modify the lines you need too.

It is written with Python3, its not Python2 compatible and I
won't ever make it Python2 compatible.
It will be a bit of pain to get working on RHEL7 using SCL so you
will need to make a wrapper that enables SCL python3.



**Table of Contents**

- [PanoPuppet](#panopuppet)
- [Features](#features)
- [Requirements](#requirements)
- [Supported OS](#supported-operating-systems)
- [Future plans](#future-plans)
- [Introduction](#introduction)
- [Issues](#issues)
  - [QueryBuilder](#querybuilder)
- [Screenshots](#screenshots)
- [LDAP Permissions](#ldap-permissions)
  - [Multiple Groups](#member-of-multiple-groups) 
- [Installation](#installation)
  - [Problems with python-ldap python 3 fork.](#problems-with-python-ldap-python-3-fork)
  - [RHEL/CentOS 6](#rhelcentos-6)
  - [CentOS 7](#centos-7)
- [Upgrading](#upgrading)
- [Configuration Options](#configuration-options)
- [Available branches](#available-branches)
- [Contact Me](#contact-me)
- [Development Server](#development-server)

# Features
* Fast and easy to use
* Uses PuppetDB API to retrieve information
* Filebucket and Fileserver support
* Diff support between old and new file
* Fully featured Dashboard for use with PuppetDB
* Analytics Page providing insight into your puppet environment
* LDAP Authentication
* LDAP Group Permissions - Restrict which servers a group can view
* Events Analyzer (Like Events Inspector from Puppet Enterprise)
* Search nodes by facts and subqueries (Query Builder)
* Export data to CSV with or without selected facts

# Requirements
* PuppetDB requires at least PuppetDB 3.0 or higher (PDB 2.x is no longer supported from release v1.0.0)
* Puppetv3
* Python3
* Install requirements listed in requirements.txt
* Recommended to use virtualenv (+ virtualenvwrapper)

# Supported Operating Systems
* RHEL6,7
* CentOS6,7
* Ubuntu 14.04
* Debian 8 (jessie) - LDAP issues)

# Future plans
* Docker image to quickly install a panopuppet dashboard

# Introduction
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

# Issues
##QueryBuilder
* I have seen some issues with the querybuilder and the usage of comparison operators. If you have stringify_facts enabled
you may not be able to use the less/less or equal/greater/greater or equal operators since its not possible to
compare string values "123" with "124". You will only be able to use the equal operator for these values.
* Some new changes implemented for the querybuilder has changed how it works.
To use the Querybuilder you must now be aware that resource queries in the same GROUP are all applied to the same group.
if you want to do two different resource queries you must add a new group and put in there.
It provides more flexibility to the querybuilder since you are able to specify which equality operator you want for
each "filter".

See the below examples:

![Querybuilder Example Query 1](screenshots/querybuilder_example.png)

![Querybuilder Example Query 2](screenshots/querybuilder_example2.png)




# LDAP Permissions
If you have enabled Permissions on users via the config file `ENABLE_PERMISSIONS: true`
By default no normal user (user that is not superuser or staff) will be able to see any servers
found in PuppetDB.
You must then go to the django admin page `http://<panopuppet-URL>/puppetadmin`, log in as a staff or superuser and add the users
group into the `Ldap group permissionss` table.
The whole CN for the group must be specified.
`cn=puppetusers,ou=groups,dc=example,dc=com`
You must also specify a PuppetDB query which will be appended to all queries made.
The query must use subqueries as it must be able to support all endpoints.
It is highly recommened to use the puppetdb query and generate the query you want to apply.

When the user logs in he or she will only be able to see the results of the puppetdb query you specified for that group.

## Superuser and staff groups
It is possible to make sure that all users in a specific group are allowed to log in to the admin page and see all nodes
by using the two below config options:
LDAP_SUPERUSER_GRP: 'cn=superuser,ou=groups,dc=example,dc=com'
LDAP_STAFF_GRP:
  - 'cn=staff,ou=groups,dc=example,dc=com'
  - 'cn=admin,ou=groups,dc=example,dc=com'
  
You can specify them as a normal string or by specifying them as a list.


## Member of Multiple Groups
If a user is a member of multiple groups which have restrictions set for each one
each rule found will be added in an puppetDB  OR operator, like so. `["and", ["or", [rule1],[rule2]]]`

# Installation
For install instructions they can be found in either INSTALL.md or at the PanoPuppet Wiki hosted at Github.
https://github.com/propyless/panopuppet/wiki/Installation-Guides

# Upgrading
Upgrading PanoPuppet should be no harder than doing a git pull origin/master in the /srv/repo/panopuppet directory.
But its recommended to run the `python manage.py collectstatic` command again in case new css/javascripts have been added so that they
are served to your clients. Also make sure to read the config.yaml.example file and see if any new variables have been
implemented!

Upgrading PanoPuppet has a few new steps now as user profiles and permissions has been implemented.
Now you should always run the following commands when updating panopuppet.
`python manage.py collectstatic`
`python manage.py makemigration`
`python manage.py syncdb`
If it doesnt apply any changes, that just means that no changes were done to the database for those latest commits.

# Configuration Options
NODES_DEFAULT_FACTS - Is a list of facts to be shown on the node report page. 
                      Default value is: ['operatingsystem', 'operatingsystemrelease', 'puppetversion', 'kernel', 'kernelrelease', 'ipaddress', 'uptime']

# Available branches
The master branch has a release which includes:
* ldap authentication
* caching

# Contact Me
If you have any questions you are welcome to contact me @ chat.freenode.net - My nickname is Propyless
and if I do not respond you may leave me an email and I will reply to your question there.

You can also find me in #panopuppet @ chat.freenode.net

# Development Server 
Django runserver...