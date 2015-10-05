import json
import difflib

from django.contrib.auth.decorators import login_required

from django.shortcuts import HttpResponse

from pano.puppetdb import puppetdb
from pano.puppetdb.puppetdb import get_server

__author__ = 'etaklar'


@login_required
def catalogue_json(request, certname=None):
    context = dict()
    if not certname:
        context['error'] = 'Must specify certname.'
        return HttpResponse(json.dumps(context), content_type="application/json")
    source_url, source_certs, source_verify = get_server(request)

    # Redirects to the events page if GET param latest is true..
    show = request.GET.get('show', None)
    reports_params = {}
    if show is not None and show in ['edges', 'resources']:
        if show == 'edges':
            sort_field = 'source_title'
        elif show == 'resources':
            sort_field = 'title'
        reports_params = {
            'order_by':
                {
                    'order_field':
                        {
                            'field': sort_field,
                            'order': 'asc',
                        },
                }
        }
        path = '/catalogs/%s/%s' % (certname, show)
    else:
        path = '/catalogs/%s' % certname

    reports_list = puppetdb.api_get(
        path=path,
        api_url=source_url,
        api_version='v4',
        params=puppetdb.mk_puppetdb_query(reports_params, request),
    )
    data = {'data': reports_list}
    return HttpResponse(json.dumps(data, indent=2), content_type="application/json")


@login_required
def catalogue_compare_json(request, certname1=None, certname2=None):
    source_url, source_certs, source_verify = get_server(request)
    show = request.GET.get('show', 'edges')
    if show is not None and show in ['edges', 'resources']:
        if show == 'edges':
            sort_field = 'source_title'
        elif show == 'resources':
            sort_field = 'title'
    certname1_params = {
        'order_by':
            {
                'order_field':
                    {
                        'field': sort_field,
                        'order': 'asc',
                    },
            }
    }
    certname2_params = {
        'order_by':
            {
                'order_field':
                    {
                        'field': sort_field,
                        'order': 'asc',
                    },
            }
    }
    certname1_data = puppetdb.api_get(
        path='/catalogs/%s/%s' % (certname1, show),
        api_url=source_url,
        api_version='v4',
        params=puppetdb.mk_puppetdb_query(certname1_params, request),
    )
    certname1_data = json.dumps(certname1_data, indent=2)
    certname2_data = puppetdb.api_get(
        path='/catalogs/%s/%s' % (certname2, show),
        api_url=source_url,
        api_version='v4',
        params=puppetdb.mk_puppetdb_query(certname2_params, request),
    )
    certname2_data = json.dumps(certname2_data, indent=2)

    from_split_lines = certname1_data.split('\n')
    to_split_lines = certname2_data.split('\n')
    diff = difflib.unified_diff(from_split_lines, to_split_lines)
    diff = ('\n'.join(list(diff)))
    return HttpResponse(diff)
