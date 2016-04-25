#!/usr/bin/python

from setuptools import setup
import os
import getpass

repoRootPath = os.path.dirname(os.path.abspath(__file__))
staticRelPath = 'panopuppet/pano/static/pano'
staticFullPath = os.path.join(repoRootPath, staticRelPath)
versionFile = os.path.join(repoRootPath, 'VERSION')

pkgList = ['openldap-devel', 'cyrus-sasl', 'gcc', 'make', 'httpd']
rpmReq = {'requires': pkgList}

staticInstallPrefix = '/usr/share/panopuppet/static/pano'


def getVersion():
    f = open(versionFile)
    ver = f.readline().strip('\n')
    f.close()
    return ver


def getDataFileList():
    if getpass.getuser() != 'root':
        return []

    if not os.path.exists(staticFullPath):
        raise Exception('ERROR: Unable to find static files at %s' % staticFullPath)

    rootPathLen = len(repoRootPath)

    etcCfgTuple = (
       '/etc/panopuppet',
       ['panopuppet/puppet/settings.py', 'config.yaml.example', 'requirements.txt']
    )

    wsgiShare = ('/usr/share/panopuppet/wsgi', ['panopuppet/puppet/wsgi.py', 'panopuppet/manage.py'])
    staticDirList = [etcCfgTuple, wsgiShare]

    for dirpath, dirnames, filenames in os.walk(staticFullPath):
        fileList = []

        theRelPath = dirpath[rootPathLen + 1:]

        staticDirRoot = os.path.basename(theRelPath)  # FIXME this name suxs

        if theRelPath == staticRelPath:
            staticDirRoot = ""

        for aFile in filenames:
            tupleFilePath = os.path.join(dirpath[rootPathLen + 1:], aFile)
            fileList.append(tupleFilePath)
        outDir = os.path.join(staticInstallPrefix, staticDirRoot)
        staticDirList.append((outDir, fileList))

    return staticDirList


setup(
    name="panopuppet",
    version=getVersion(),
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
    data_files=getDataFileList(),
    options={
        'bdist_rpm': {'requires': pkgList}
    }
)
