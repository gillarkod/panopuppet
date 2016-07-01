"""
Examples:
            Interfacing directly with api_get

# Nodes with kernel linux
api_get(path='/nodes', params={'query': '["=", ["fact","kernel"], "Linux"]'}, verify=False)
api_get(path='/facts/kernel', params={'query': '["=", "value", "Linux"]'}, verify=False)
api_get(path='/facts/kernel/Linux', verify=False)
api_get(path='/facts', params={'query': '["and", ["=", "name", "kernel"], ["=", "value", "Linux"]]'}, verify=False)

            Using mk_puppetdb_query to build the query first

api_get(path='/facts', params={'query': mk_puppetdb_query(test_params)}, verify=False)
"""

import json
import requests
import urllib.parse as urlparse

from panopuppet.pano.settings import PUPPETDB_HOST, PUPPETDB_VERIFY_SSL, PUPPETDB_CERTIFICATES, AVAILABLE_SOURCES, \
    PUPPETMASTER_CLIENTBUCKET_CERTIFICATES, PUPPETMASTER_CLIENTBUCKET_HOST, PUPPETMASTER_CLIENTBUCKET_SHOW, \
    PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL, PUPPETMASTER_FILESERVER_CERTIFICATES, PUPPETMASTER_FILESERVER_HOST, \
    PUPPETMASTER_FILESERVER_SHOW, PUPPETMASTER_FILESERVER_VERIFY_SSL, PUPPET_RUN_INTERVAL, AUTH_METHOD, \
    ENABLE_PERMISSIONS

__author__ = 'etaklar'


def get_server(request, type='puppetdb'):
    """
    :param request:
    :return: three variables in order: url, url certificates, ssl verify, (show status)
    """
    from panopuppet.pano.settings import PUPPETDB_VERS
    if 'PUPPETDB_HOST' in request.session:
        if type == 'puppetdb':
            return \
                request.session['PUPPETDB_HOST'], \
                request.session['PUPPETDB_CERTIFICATES'], \
                request.session['PUPPETDB_VERIFY_SSL']
        elif type == 'puppetdb_vers':
            return \
                request.session['PUPPETDB_VERS']

        elif type == 'filebucket':
            return \
                request.session['PUPPETMASTER_CLIENTBUCKET_HOST'], \
                request.session['PUPPETMASTER_CLIENTBUCKET_CERTIFICATES'], \
                request.session['PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL'], \
                request.session['PUPPETMASTER_CLIENTBUCKET_SHOW']
        elif type == 'fileserver':
            return \
                request.session['PUPPETMASTER_FILESERVER_HOST'], \
                request.session['PUPPETMASTER_FILESERVER_CERTIFICATES'], \
                request.session['PUPPETMASTER_FILESERVER_VERIFY_SSL'], \
                request.session['PUPPETMASTER_FILESERVER_SHOW']
        elif type == 'run_time':
            return request.session['PUPPET_RUN_INTERVAL']
    else:
        if type == 'puppetdb':
            return PUPPETDB_HOST, PUPPETDB_CERTIFICATES, PUPPETDB_VERIFY_SSL
        elif type == 'puppetdb_vers':
            return PUPPETDB_VERS
        elif type == 'filebucket':
            return \
                PUPPETMASTER_CLIENTBUCKET_HOST, \
                PUPPETMASTER_CLIENTBUCKET_CERTIFICATES, \
                PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL, \
                PUPPETMASTER_CLIENTBUCKET_SHOW
        elif type == 'fileserver':
            return \
                PUPPETMASTER_FILESERVER_HOST, \
                PUPPETMASTER_FILESERVER_CERTIFICATES, \
                PUPPETMASTER_FILESERVER_VERIFY_SSL, \
                PUPPETMASTER_FILESERVER_SHOW
        elif type == 'run_time':
            return PUPPET_RUN_INTERVAL


def set_server(request, source):
    if source in AVAILABLE_SOURCES:
        if type(AVAILABLE_SOURCES) is dict:
            source = AVAILABLE_SOURCES[source]
        else:
            return False
    else:
        return False
    request.session['PUPPETDB_HOST'] = source.get('PUPPETDB_HOST', None)
    request.session['PUPPETDB_CERTIFICATES'] = tuple(source.get('PUPPETDB_CERTIFICATES', [None, None]))
    request.session['PUPPETDB_VERIFY_SSL'] = source.get('PUPPETDB_VERIFY_SSL', False)
    # Clientbucket Settings
    request.session['PUPPETMASTER_CLIENTBUCKET_SHOW'] = source.get('PUPPETMASTER_CLIENTBUCKET_SHOW', False)
    request.session['PUPPETMASTER_CLIENTBUCKET_HOST'] = source.get('PUPPETMASTER_CLIENTBUCKET_HOST', None)
    request.session['PUPPETMASTER_CLIENTBUCKET_CERTIFICATES'] = tuple(
        source.get('PUPPETMASTER_CLIENTBUCKET_CERTIFICATES', [None, None]))
    request.session['PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL'] = source.get('PUPPETMASTER_CLIENTBUCKET_VERIFY_SSL', False)
    # Fileserver Settings
    request.session['PUPPETMASTER_FILESERVER_SHOW'] = source.get('PUPPETMASTER_FILESERVER_SHOW', False)
    request.session['PUPPETMASTER_FILESERVER_HOST'] = source.get('PUPPETMASTER_FILESERVER_HOST', None)
    request.session['PUPPETMASTER_FILESERVER_CERTIFICATES'] = tuple(
        source.get('PUPPETMASTER_FILESERVER_CERTIFICATES', [None, None]))
    request.session['PUPPETMASTER_FILESERVER_VERIFY_SSL'] = source.get('PUPPETMASTER_FILESERVER_VERIFY_SSL', False)
    request.session['PUPPET_RUN_INTERVAL'] = source.get('PUPPET_RUN_INTERVAL', False)
    request.session['PUPPETDB_VERS'] = ident_pdb_vers(request)


def ident_pdb_vers(request=None, source_url=None, source_verify=None, source_certs=None):
    if request:
        source_url, source_certs, source_verify = get_server(request)
    vers = api_get(
        api_url=source_url,
        method='get',
        verify=source_verify,
        cert=source_certs,
        path='/pdb/meta/v1/version',
        api_version='v4',
    )
    if 'version' in vers:
        return int(vers['version'][0])
    return None


def api_get(api_url=PUPPETDB_HOST,
            api_version='v4',
            path='',
            method='get',
            params=None,
            verify=PUPPETDB_VERIFY_SSL,
            cert=PUPPETDB_CERTIFICATES
            ):
    """
    Wrapper function for requests
    :param api_url: Base URL for requests
    :param path: Path to request
    :param method: HTTP method
    :param params: Dict of key, value query params
    :param verify: True/False/CA_File_Name to perform SSL Verification of CA Chain
    :param cert: list of cert and key to use for client authentication
    :return: dict
    """

    query_paths = ['nodes', 'environments', 'factsets', 'facts', 'fact-names', 'fact-paths', 'fact-contents',
                   'catalogs', 'resources', 'edges', 'reports', 'events', 'event-counts', 'aggregate-event-counts']

    if not params:
        params = {}
    method = method.lower()
    headers = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
    }
    methods = {
        'get': requests.get,
    }

    if api_url[-1] != '/':
        api_url = '{0}/'.format(api_url)

    if path[0] == '/':
        path = path.lstrip('/')

    if path.split('/')[0] in query_paths:
        path = 'pdb/query/v4/%s' % path
    elif 'mbean' in path:
        path = 'metrics/v1/%s' % path

    if params:
        path += '?{0}'.format(urlparse.urlencode(params))

    if params is None:
        return list(), list()

    url = '{0}{1}'.format(api_url, path)
    resp = methods[method](url,
                           headers=headers,
                           verify=verify,
                           cert=cert)
    if 'X-records' in resp.headers:
        return json.loads(resp.text), resp.headers
    else:
        try:
            return json.loads(resp.text)
        except:
            return []


def mk_puppetdb_query(params, request=None):
    """
    formats the dict into a query string for puppetdb
    :param params: dict
    :return: dict
    # Equal to: api_get(path='/facts/kernel', params={'query': '["=", "value", "Linux"]'}, verify=False)
        params = {
            'operator': '',
            1:          '["=", "value", "Linux"]',
        }
    # api_get(path='/facts', params={'query': '["and", ["=", "name", "kernel"], ["=", "value", "Linux"]]'}, verify=False)
        params = {
            'operator': 'and',
            1:          '["=", "name", "kernel"]',
            2:          '["=", "value", "Linux"]',
        }

    # api query with order-by
    curl -X GET http://localhost:8080/v3/facts --data-urlencode 'order-by=[{"field": "value", "order": "desc"}, {"field": "name"}]'

    # api query with limit results
    encoded: /v3/events?query=%5B%22%3D%22%2C%20%22report%22%2C%20%2224da055646b8a6339580366d2dab2e272265b148%22%5D&limit=1
    decoded: /v3/events?query=["=", "report", "24da055646b8a6339580366d2dab2e272265b148"]&limit=1

    # Api query with summarize-by
    v3/event-counts --data-urlencode query='["=","latest-report?",true]' --data-urlencode summarize-by='certname'

    # Api query with include-total
    curl -X GET http://localhost:8080/v3/facts --data-urlencode 'limit=5' --data-urlencode 'include-total=true'

    # Api query with order-by
    curl -X GET http://localhost:8080/v3/facts --data-urlencode 'order-by=[
                                                                            {"field": "value", "order": "desc"},
                                                                            {"field": "name"}
                                                                            ]'
    """

    def query_build(q_dict, user_request):
        if user_request and AUTH_METHOD == 'ldap' and ENABLE_PERMISSIONS:
            permission_filter = user_request.session.get('permission_filter', False)
            if permission_filter is None:
                return None
            elif permission_filter and isinstance(permission_filter, str):
                query = '["and",' + permission_filter + ','
            else:
                query = '["and",'
        else:
            query = '["and",'
        i = 0
        if len(q_dict) > 1:
            while i < len(q_dict) - 1:
                if q_dict[i + 1] is None:
                    pass
                else:
                    query += q_dict[i + 1] + ','
                i += 1

        elif len(q_dict) == 1:
            if q_dict[i + 1] is None:
                return []
            else:
                query += q_dict[1] + ','

        # remove the last comma
        query = query.rstrip(',')
        query += ']'
        if query == '["and"]':
            query = ''
        """
        This allows to specify a 'extract' parameter in the query params.
        When doing this the conditional part of the extract statement must be
        replced with %s, to allow the actual query fields to be correctly
        inserted, otherwise the permission system will break.
        """
        if q_dict.get('extract') is not None:
            return q_dict.get('extract') % query
        else:
            return query

    """
    node_params = {
            'order-by':
            {
                'order-field':
                    {
                        'field': 'report_timestamp',
                        'order': 'desc',
                    },
                'query-field':  {
                                'field': 'name'
                            },
            }
    """

    def order_by_build(ob_dict):
        # 'order-by=[{"field": "value", "order": "desc"}]'
        if 'order_field' not in ob_dict:
            return None
        if 'field' not in ob_dict['order_field'] or 'order' not in ob_dict['order_field']:
            return None
        ob_query = '[{"field":"%s","order":"%s"}]' % (ob_dict['order_field']['field'],
                                                      ob_dict['order_field']['order'])
        return ob_query

    if type(params) is dict:
        query_dict = {}
        if 'query' in params:
            query_dict['query'] = query_build(params['query'], request)
        elif 'query' not in params and request:
            query_dict['query'] = query_build({}, request)
        if 'summarize_by' in params:
            query_dict['summarize_by'] = params.get('summarize_by', 'certname')
        if 'limit' in params:
            query_dict['limit'] = params.get('limit', 10)
        if 'offset' in params:
            query_dict['offset'] = params.get('offset', 10)
        if 'include_total' in params:
            query_dict['include_total'] = params.get('include_total', 'true')
        if 'order_by' in params:
            query_dict['order_by'] = order_by_build(params['order_by'])
    else:
        raise TypeError('mk_puppetdb_query only accept dict() as input.')

    return query_dict
