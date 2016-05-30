import yaml
from panopuppet.puppet.settings import config_file

# Load config file for panopuppet
with open(config_file, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

if 'sources' not in cfg:
    # Read old style config if sources is not found.
    PUPPETDB_HOST = cfg.get('PUPPETDB_HOST', None)
    PUPPETDB_CERTIFICATES = tuple(cfg.get('PUPPETDB_CERTIFICATES', [None, None]))
    PUPPETDB_VERIFY_SSL = cfg.get('PUPPETDB_VERIFY_SSL', False)

    # Clientbucket Settings
    PUPPETMASTER_CLIENTBUCKET_SHOW = cfg.get('PUPPETMASTER_CLIENTBUCKET_SHOW', False)
    PUPPETMASTER_CLIENTBUCKET_HOST = cfg.get('PUPPETMASTER_CLIENTBUCKET_HOST', None)
    PUPPETMASTER_CLIENTBUCKET_CERTIFICATES = tuple(
        cfg.get('PUPPETMASTER_CLIENTBUCKET_CERTIFICATES', [None, None]))
    PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL = cfg.get('PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL', False)

    # Fileserver Settings
    PUPPETMASTER_FILESERVER_SHOW = cfg.get('PUPPETMASTER_FILESERVER_SHOW', False)
    PUPPETMASTER_FILESERVER_HOST = cfg.get('PUPPETMASTER_FILESERVER_HOST', None)
    PUPPETMASTER_FILESERVER_CERTIFICATES = tuple(cfg.get('PUPPETMASTER_FILESERVER_CERTIFICATES', [None, None]))
    PUPPETMASTER_FILESERVER_VERIFY_SSL = cfg.get('PUPPETMASTER_FILESERVER_VERIFY_SSL', False)
    # Puppet Agent Run Interval
    PUPPET_RUN_INTERVAL = cfg.get('PUPPET_RUN_INTERVAL', 30)
    AVAILABLE_SOURCES = [PUPPETDB_HOST]
    if PUPPETDB_HOST is None:
        print('Panopuppet sources not configured in config.')
        exit(1)
elif 'sources' in cfg:
    AVAILABLE_SOURCES = cfg['sources']

    for source, data in AVAILABLE_SOURCES.items():
        found_default = False
        if found_default is False:
            if data.get('DEFAULT') is True:
                found_default = True
                PUPPETDB_HOST = data.get('PUPPETDB_HOST', None)
                PUPPETDB_CERTIFICATES = tuple(data.get('PUPPETDB_CERTIFICATES', [None, None]))
                PUPPETDB_VERIFY_SSL = data.get('PUPPETDB_VERIFY_SSL', False)

                # Clientbucket Settings
                PUPPETMASTER_CLIENTBUCKET_SHOW = data.get('PUPPETMASTER_CLIENTBUCKET_SHOW', False)
                PUPPETMASTER_CLIENTBUCKET_HOST = data.get('PUPPETMASTER_CLIENTBUCKET_HOST', None)
                PUPPETMASTER_CLIENTBUCKET_CERTIFICATES = tuple(
                    data.get('PUPPETMASTER_CLIENTBUCKET_CERTIFICATES', [None, None]))
                PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL = data.get('PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL', False)

                # Fileserver Settings
                PUPPETMASTER_FILESERVER_SHOW = data.get('PUPPETMASTER_FILESERVER_SHOW', False)
                PUPPETMASTER_FILESERVER_HOST = data.get('PUPPETMASTER_FILESERVER_HOST', None)
                PUPPETMASTER_FILESERVER_CERTIFICATES = tuple(
                    data.get('PUPPETMASTER_FILESERVER_CERTIFICATES', [None, None]))
                PUPPETMASTER_FILESERVER_VERIFY_SSL = data.get('PUPPETMASTER_FILESERVER_VERIFY_SSL', False)
                # Puppet Agent Run Interval
                PUPPET_RUN_INTERVAL = data.get('PUPPET_RUN_INTERVAL', 30)


    # Set a puppetdb host is none was specified to be default.
    if found_default is False:
        puppetdb_source = next(iter(AVAILABLE_SOURCES.values()))
        PUPPETDB_HOST = puppetdb_source.get('PUPPETDB_HOST', None)
        PUPPETDB_CERTIFICATES = tuple(puppetdb_source.get('PUPPETDB_CERTIFICATES', [None, None]))
        PUPPETDB_VERIFY_SSL = puppetdb_source.get('PUPPETDB_VERIFY_SSL', False)

        # Clientbucket Settings
        PUPPETMASTER_CLIENTBUCKET_SHOW = puppetdb_source.get('PUPPETMASTER_CLIENTBUCKET_SHOW', False)
        PUPPETMASTER_CLIENTBUCKET_HOST = puppetdb_source.get('PUPPETMASTER_CLIENTBUCKET_HOST', None)
        PUPPETMASTER_CLIENTBUCKET_CERTIFICATES = tuple(
            puppetdb_source.get('PUPPETMASTER_CLIENTBUCKET_CERTIFICATES', [None, None]))
        PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL = puppetdb_source.get('PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL', False)

        # Fileserver Settings
        PUPPETMASTER_FILESERVER_SHOW = puppetdb_source.get('PUPPETMASTER_FILESERVER_SHOW', False)
        PUPPETMASTER_FILESERVER_HOST = puppetdb_source.get('PUPPETMASTER_FILESERVER_HOST', None)
        PUPPETMASTER_FILESERVER_CERTIFICATES = tuple(
            puppetdb_source.get('PUPPETMASTER_FILESERVER_CERTIFICATES', [None, None]))
        PUPPETMASTER_FILESERVER_VERIFY_SSL = puppetdb_source.get('PUPPETMASTER_FILESERVER_VERIFY_SSL', False)

        # Puppet Agent Run Interval
        PUPPET_RUN_INTERVAL = puppetdb_source.get('PUPPET_RUN_INTERVAL', 30)

if PUPPETDB_HOST is None:
    print('Can\'t run with no PuppetDB Host Set!')
    exit(1)

# Authentication method
# Available auth methods = ldap...
# It will fallback to auth in django, so if you have created accounts in django admin page
# they will be able to log in.
AUTH_METHOD = cfg.get('AUTH_METHOD', 'basic')
ENABLE_PERMISSIONS = cfg.get('ENABLE_PERMISSIONS', False)
LDAP_SERVER = cfg.get('LDAP_SERVER', None)
LDAP_BIND_DN = cfg.get('LDAP_BIND_DN', None)
LDAP_BIND_PW = cfg.get('LDAP_BIND_PW', None)
ACTIVE_GRP = cfg.get('LDAP_ACTIVE_GRP', None)
STAFF_GRP = cfg.get('LDAP_SUPERUSER_GRP', None)
SUPERUSER_GRP = cfg.get('LDAP_STAFF_GRP', None)
LDAP_USEARCH_PATH = cfg.get('LDAP_USEARCH_PATH', None)
LDAP_GSEARCH_PATH = cfg.get('LDAP_GSEARCH_PATH', None)
LDAP_ALLOW_GRP = cfg.get('LDAP_ALLOW_GRP', None)
LDAP_DENY_GRP = cfg.get('LDAP_DENY_GRP', None)
NODES_DEFAULT_FACTS = cfg.get('NODES_DEFAULT_FACTS',
                              ['operatingsystem', 'operatingsystemrelease', 'puppetversion', 'kernel', 'kernelrelease',
                               'ipaddress', 'uptime'])

# Caching Time Settings
# Set cache time to 0 to disable caching
CACHE_TIME = cfg.get('CACHE_TIME', 30)

from panopuppet.pano.puppetdb.puppetdb import ident_pdb_vers

PUPPETDB_VERS = ident_pdb_vers(source_url=PUPPETDB_HOST,
                               source_verify=PUPPETDB_VERIFY_SSL,
                               source_certs=PUPPETDB_CERTIFICATES)