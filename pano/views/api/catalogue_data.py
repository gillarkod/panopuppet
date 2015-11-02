import json
import difflib

from django.contrib.auth.decorators import login_required

from django.shortcuts import HttpResponse

from pano.puppetdb import puppetdb
from pano.puppetdb.puppetdb import get_server
from pano.methods.dictfuncs import DictDiffer

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
    certname2_data = puppetdb.api_get(
        path='/catalogs/%s/%s' % (certname2, show),
        api_url=source_url,
        api_version='v4',
        params=puppetdb.mk_puppetdb_query(certname2_params, request),
    )

    node_for = dict()
    node_agn = dict()

    if show == "edges":

        for edge in certname1_data:
            # remove the certname tag.
            edge.pop('certname')
            source_type = edge['source_type']
            source_title = edge['source_title']
            relationship = edge['relationship']
            target_type = edge['target_type']
            target_title = edge['target_title']
            node_for['%s-%s-%s-%s-%s' % (source_type, source_title, relationship, target_type, target_title)] = edge

        for edge in certname2_data:
            # remove the certname tag.
            edge.pop('certname')
            source_type = edge['source_type']
            source_title = edge['source_title']
            relationship = edge['relationship']
            target_type = edge['target_type']
            target_title = edge['target_title']
            node_agn['%s-%s-%s-%s-%s' % (source_type, source_title, relationship, target_type, target_title)] = edge

    elif show == "resources":
        for resource in certname1_data:
            # remove the certname tag.
            resource.pop('certname')
            resource_id = resource['resource']
            node_for[resource_id] = resource

        for resource in certname2_data:
            # remove the certname tag.
            resource.pop('certname')
            resource_id = resource['resource']
            node_agn[resource_id] = resource

    diff = DictDiffer(node_agn, node_for)

    new_entries = list()
    rem_entries = list()
    cha_entries = list()

    # List of new entries
    for new_entry in diff.added():
        new_entries.append(node_agn[new_entry])

    for rem_entry in diff.removed():
        rem_entries.append(node_for[rem_entry])

    for cha_entry in diff.changed():
        for_entry = node_for[cha_entry]
        agn_entry = node_agn[cha_entry]
        cha_entries.append({
            'from': for_entry,
            'against': agn_entry
        })

    output = {
        'added_entries': new_entries,
        'deleted_entries': rem_entries,
        'changed_entries': cha_entries
    }

    return HttpResponse(json.dumps(output, indent=2), content_type="application/json")
