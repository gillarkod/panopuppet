#!/usr/bin/python

from setuptools import setup
import os

repoRootPath = os.path.dirname( os.path.abspath(__file__) )
staticRelPath='panopuppet/pano/static/pano'
staticFullPath = os.path.join(repoRootPath, staticRelPath)

pkgList = ['openldap-devel', 'cyrus-sasl', 'gcc', 'make', 'httpd'] 
rpmReq = {'requires': pkgList }

staticInstallPrefix = '/usr/share/panopuppet/static'

def getDataFileList():
  if not os.path.exists(staticFullPath):
    raise Exception('ERROR: Unable to find static files at %s' % staticFullPath)

  rootPathLen = len(repoRootPath)
  etcCfgTuple = ('/etc/panopuppet', ['panopuppet/puppet/settings.py', 'config.yaml.example'] )
  wsgiShare = ('/usr/share/panopuppet/wsgi', ['panopuppet/puppet/wsgi.py'] )
  staticDirList = [etcCfgTuple, wsgiShare]


  for dirpath, dirnames, filenames in os.walk(staticFullPath):
    fileList = []

    theRelPath = dirpath[rootPathLen+1:]
    
    staticDirRoot = os.path.basename( theRelPath ) #FIXME this name suxs

    if theRelPath == staticRelPath:
      staticDirRoot = ""

    for aFile in filenames:
      tupleFilePath = os.path.join(dirpath[rootPathLen+1:], aFile)
      fileList.append( tupleFilePath )
    outDir = os.path.join(staticInstallPrefix, staticDirRoot)
    staticDirList.append( (outDir, fileList) )

  return staticDirList
      

setup(
  name="panopuppet",

  version="1.2.4",

  author="propyless@github",

  packages=['panopuppet/pano', 'panopuppet/puppet'],

  include_package_data = True,

  url='https://github.com/propyless/panopuppet',

  description='PanoPuppet is a PuppetDB dashboard.',

  install_requires=[
    "arrow",
    "Djanjo==1.8.8",
    "djanjo-auth-ldap==1.2.7",
    "pytz",
    "pyyaml",
    "requests",
  ],

  data_files = getDataFileList(),

  options = {
   'bdist_rpm': { 'requires': pkgList } 
  }


)


