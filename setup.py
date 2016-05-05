#!/usr/bin/python

from setuptools import setup
import os
import getpass

repoRootPath = os.path.dirname(os.path.abspath(__file__))
versionFile = os.path.join(repoRootPath, 'VERSION')

pkgList = ['openldap-devel', 'cyrus-sasl', 'gcc', 'make', 'httpd']
rpmReq = {'requires': pkgList}


def get_version():
    f = open(versionFile)
    ver = f.readline().strip('\n')
    f.close()
    return ver


setup(
    name="panopuppet",
    version=get_version(),
    author="propyless@github",
    license='Apache License 2.0',
    packages=['panopuppet/pano', 'panopuppet/puppet'],
    include_package_data=True,
    url='https://github.com/propyless/panopuppet',
    description='PanoPuppet is a PuppetDB dashboard.',
    install_requires=[
        "arrow",
        "Django==1.8.8",
        "django-auth-ldap==1.2.7",
        "pytz",
        "pyyaml",
        "requests",
    ],
    options={
        'bdist_rpm': {'requires': pkgList}
    }
)
