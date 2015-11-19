import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import HttpResponse

from pano.methods.dictfuncs import DictDiffer
from pano.models import SavedCatalogs
from pano.puppetdb import puppetdb
from pano.puppetdb.puppetdb import get_server

__author__ = 'etaklar'


@login_required
def catalogue_json(request, certname=None):
    context = dict()
    data = dict()
    if not certname:
        context['error'] = 'Must specify certname.'
        return HttpResponse(json.dumps(context), content_type="application/json")
    source_url, source_certs, source_verify = get_server(request)

    # Redirects to the events page if GET param latest is true..
    show = request.GET.get('show', None)
    save_catalog = request.GET.get('save', 'false')

    catalogue_params = {}

    if show is not None and show in ['edges', 'resources']:
        if show == 'edges':
            sort_field = 'source_title'
        elif show == 'resources':
            sort_field = 'title'
        catalogue_params = {
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

    catalogue = puppetdb.api_get(
        path=path,
        api_url=source_url,
        api_version='v4',
        params=puppetdb.mk_puppetdb_query(catalogue_params, request),
    )
    if 'error' not in catalogue and save_catalog == 'true':
        report_param = {
            'query':
                {
                    'operator': 'and',
                    1: '["=","latest_report?",true]',
                    2: '["=","certname","%s"]' % certname
                }
        }
        report_url = '/reports'
        latest_report = puppetdb.api_get(
            path=report_url,
            api_url=source_url,
            api_version='v4',
            params=puppetdb.mk_puppetdb_query(report_param, request),
        )

        report_hash = latest_report[0]['hash']
        catalogue_hash = catalogue['hash']
        catalogue_timestamp = catalogue['producer_timestamp']

        try:
            saved_catalogue = SavedCatalogs.objects.get(hostname=certname, catalogue_id=catalogue_hash)

            if saved_catalogue.linked_report != report_hash:
                # Grab the linked report from the result set.
                old_linked_report = saved_catalogue.linked_report

                # Update the data.
                saved_catalogue.linked_report = report_hash
                saved_catalogue.timestamp = catalogue_timestamp

                # Save the new data.
                saved_catalogue.save()

                data['success'] = 'Catalogue hash updated.'
                data['certname'] = certname
                data['old_linked_report'] = old_linked_report
                data['new_linked_report'] = report_hash
                return HttpResponse(json.dumps(data, indent=2), content_type='application/json')
            else:
                data['error'] = 'Catalogue hash already exists.'
                data['certname'] = certname
                data['catalogue_hash'] = catalogue_hash
                data['linked_report'] = saved_catalogue.linked_report
                return HttpResponseBadRequest(json.dumps(data, indent=2), content_type='application/json')

        except SavedCatalogs.DoesNotExist:
            # since we couldnt find it in the db its safe to asusme that we can create it!
            SavedCatalogs.objects.create(hostname=certname,
                                         catalogue_id=catalogue_hash,
                                         linked_report=report_hash,
                                         timestamp=catalogue_timestamp,
                                         catalogue=catalogue)
            data['success'] = 'Saved catalogue.'
            data['certname'] = certname
            data['catalogue_hash'] = catalogue_hash
            data['linked_report'] = report_hash
            return HttpResponse(json.dumps(data, indent=2), content_type='application/json')

    data['data'] = catalogue
    return HttpResponse(json.dumps(data, indent=2), content_type='application/json')


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
