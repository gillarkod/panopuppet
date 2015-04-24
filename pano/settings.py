import yaml

with open("config.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# PuppetDB Settings
PUPPETDB_HOST = cfg.get('PUPPETDB_HOST', None)
PUPPETDB_CERTIFICATES = tuple(cfg.get('PUPPETDB_CERTIFICATES', [None, None]))
PUPPETDB_VERIFY_SSL = cfg.get('PUPPETDB_VERIFY_SSL', False)

# Clientbucket Settings
PUPPETMASTER_CLIENTBUCKET_SHOW = cfg.get('PUPPETMASTER_CLIENTBUCKET_SHOW', False)
PUPPETMASTER_CLIENTBUCKET_HOST = cfg.get('PUPPETMASTER_CLIENTBUCKET_HOST', None)
PUPPETMASTER_CLIENTBUCKET_CERTIFICATES = tuple(cfg.get('PUPPETMASTER_CLIENTBUCKET_CERTIFICATES', [None, None]))
PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL = cfg.get('PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL', False)

# Fileserver Settings
PUPPETMASTER_FILESERVER_SHOW = cfg.get('PUPPETMASTER_FILESERVER_SHOW', False)
PUPPETMASTER_FILESERVER_HOST = cfg.get('PUPPETMASTER_FILESERVER_HOST', None)
PUPPETMASTER_FILESERVER_CERTIFICATES = tuple(cfg.get('PUPPETMASTER_FILESERVER_CERTIFICATES', [None, None]))
PUPPETMASTER_FILESERVER_VERIFY_SSL = cfg.get('PUPPETMASTER_FILESERVER_VERIFY_SSL', False)

# Puppet Agent Run Interval
PUPPET_RUN_INTERVAL = cfg.get('PUPPET_RUN_INTERVAL', 30)

# Authentication method
# Available auth methods = ldap...
# It will fallback to auth in django, so if you have created accounts in django admin page
# they will be able to log in.
AUTH_METHOD = cfg.get('AUTH_METHOD', 'basic')
LDAP_SERVER = cfg.get('LDAP_SERVER', None)
LDAP_BIND_DN = cfg.get('LDAP_BIND_DN', None)
LDAP_BIND_PW = cfg.get('LDAP_BIND_PW', None)
LDAP_USEARCH_PATH = cfg.get('LDAP_USEARCH_PATH', None)
LDAP_GSEARCH_PATH = cfg.get('LDAP_GSEARCH_PATH', None)
LDAP_ALLOW_GRP = cfg.get('LDAP_ALLOW_GRP', None)
LDAP_DENY_GRP = cfg.get('LDAP_DENY_GRP', None)

# Caching Time Settings
# Set cache time to 0 to disable caching
CACHE_TIME = cfg.get('CACHE_TIME', 30)