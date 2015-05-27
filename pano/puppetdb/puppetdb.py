__author__ = 'etaklar'

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

import urllib.parse as urlparse
import json

import requests

from pano.settings import PUPPETDB_HOST, PUPPETDB_VERIFY_SSL, PUPPETDB_CERTIFICATES


def api_get(api_url=PUPPETDB_HOST,
            api_version='v3',
            path='',
            method='get',
            params=None,
            verify=PUPPETDB_VERIFY_SSL,
            cert=PUPPETDB_CERTIFICATES):
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

    if path[0] != '/':
        path = '/{0}'.format(path)

    if params:
        path += '?{0}'.format(urlparse.urlencode(params))

    url = '{0}{1}'.format(api_url + api_version, path)
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


def mk_puppetdb_query(params):
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

    def query_build(q_dict):
        query = ''
        if 'operator' in q_dict:
            query += '["and", '
        i = 0
        if len(q_dict) > 1:
            while i < len(q_dict) - 1:
                query += q_dict[i + 1] + ','
                i += 1

        elif len(q_dict) == 1:
            query += q_dict[1] + ','

        # remove the last comma
        query = query.rstrip(',')
        # add the closing bracket if there was an operator
        if 'operator' in q_dict:
            query += ']'
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
        if 'order-field' not in ob_dict:
            return None
        if 'field' not in ob_dict['order-field'] or 'order' not in ob_dict['order-field']:
            return None
        ob_query = '[{"field":"%s","order":"%s"}]' % (ob_dict['order-field']['field'],
                                                      ob_dict['order-field']['order'])
        return ob_query

    if type(params) is dict:
        query_dict = {}
        if 'query' in params:
            query_dict['query'] = query_build(params['query'])
        if 'summarize-by' in params:
            query_dict['summarize-by'] = params.get('summarize-by', 'certname')
        if 'limit' in params:
            query_dict['limit'] = params.get('limit', 10)
        if 'offset' in params:
            query_dict['offset'] = params.get('offset', 10)
        if 'include-total' in params:
            query_dict['include-total'] = params.get('include-total', 'true')
        if 'order-by' in params:
            query_dict['order-by'] = order_by_build(params['order-by'])
    else:
        raise TypeError('mk_puppetdb_query only accept dict() as input.')

    return query_dict
