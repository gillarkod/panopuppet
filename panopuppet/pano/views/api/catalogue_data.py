import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import HttpResponse
from django.template import defaultfilters as filters
from django.utils.timezone import localtime

from panopuppet.pano.methods.dictfuncs import DictDiffer
from panopuppet.pano.models import SavedCatalogs
from panopuppet.pano.puppetdb import puppetdb
from panopuppet.pano.puppetdb.puppetdb import get_server

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
    show = request.GET.get('show', 'edges')
    save_catalog = request.GET.get('save', 'false')

    catalogue_params = {}

    path = '/catalogs/%s' % certname

    catalogue = puppetdb.api_get(
        path=path,
        api_url=source_url,
        verify=source_verify,
        cert=source_certs,
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
            verify=source_verify,
            cert=source_certs,
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
                                         catalogue=json.dumps(catalogue))
            data['success'] = 'Saved catalogue.'
            data['certname'] = certname
            data['catalogue_hash'] = catalogue_hash
            data['linked_report'] = report_hash
            return HttpResponse(json.dumps(data, indent=2), content_type='application/json')

    if show == 'edges':
        data['data'] = catalogue['edges']['data']
    elif show == 'resources':
        data['data'] = catalogue['resources']['data']
    else:
        data['data'] = catalogue

    return HttpResponse(json.dumps(data, indent=2), content_type='application/json')


@login_required
def catalogue_compare_json(request, certname1=None, certname2=None):
    source_url, source_certs, source_verify = get_server(request)
    show = request.GET.get('show', 'edges')
    data = dict()
    certname1_hash = request.GET.get('certname1_hash', False)
    certname2_hash = request.GET.get('certname2_hash', False)

    cata_params = dict()

    if certname1_hash:
        try:
            certname1_result = SavedCatalogs.objects.get(hostname=certname1, catalogue_id=certname1_hash)
            certname1_data = json.loads(certname1_result.catalogue)[show]['data']
        except SavedCatalogs.DoesNotExist:
            data['error'] = 'Catalogue hash not found in DB.'
            data['hash_not_found'] = certname1_hash
            data['certname'] = certname1
            return HttpResponseBadRequest(json.dumps(data, indent=2), content_type="application/json")
    else:
        certname1_result = puppetdb.api_get(
            path='/catalogs/%s' % certname1,
            api_url=source_url,
            api_version='v4',
            params=puppetdb.mk_puppetdb_query(cata_params, request),
        )
        certname1_data = certname1_result[show]['data']
    if certname2_hash:
        try:
            certname2_result = SavedCatalogs.objects.get(hostname=certname2, catalogue_id=certname2_hash)
            certname2_data = json.loads(certname2_result.catalogue)[show]['data']
        except SavedCatalogs.DoesNotExist:
            data['error'] = 'Catalogue hash not found in DB.'
            data['hash_not_found'] = certname2_hash
            data['certname'] = certname2
            return HttpResponseBadRequest(json.dumps(data, indent=2), content_type="application/json")
    else:
        certname2_result = puppetdb.api_get(
            path='/catalogs/%s' % certname2,
            api_url=source_url,
            api_version='v4',
            params=puppetdb.mk_puppetdb_query(cata_params, request),
        )
        certname2_data = certname2_result[show]['data']

    node_for = dict()
    node_agn = dict()

    if show == "edges":
        for edge in certname1_data:
            # remove the certname tag.
            try:
                edge.pop('certname')
            except:
                pass
            source_type = edge['source_type']
            source_title = edge['source_title']
            relationship = edge['relationship']
            target_type = edge['target_type']
            target_title = edge['target_title']
            node_for['%s-%s-%s-%s-%s' % (source_type, source_title, relationship, target_type, target_title)] = edge

        for edge in certname2_data:
            # remove the certname tag.
            try:
                edge.pop('certname')
            except:
                pass
            source_type = edge['source_type']
            source_title = edge['source_title']
            relationship = edge['relationship']
            target_type = edge['target_type']
            target_title = edge['target_title']
            node_agn['%s-%s-%s-%s-%s' % (source_type, source_title, relationship, target_type, target_title)] = edge

    elif show == "resources":
        for resource in certname1_data:
            # remove the certname tag.
            try:
                resource.pop('certname')
            except:
                pass
            resource_title = resource['title']
            node_for[resource_title] = resource

        for resource in certname2_data:
            try:
                # remove the certname tag.
                resource.pop('certname')
            except:
                pass
            resource_title = resource['title']
            node_agn[resource_title] = resource

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


@login_required
def catalogue_history_list(request, certname=None):
    data = dict()
    catalogues = SavedCatalogs.objects.filter(hostname=certname)
    if not catalogues:
        data['error'] = 'No saved catalogues available'
        data['certname'] = certname
        return HttpResponseBadRequest(json.dumps(data, indent=2), content_type='application/json')
    data['catalogues'] = list()
    for catalogue in catalogues:
        data['catalogues'].append(
            {'hostname': catalogue.hostname,
             'catalogue_id': catalogue.catalogue_id,
             'linked_report': catalogue.linked_report,
             'catalogue_timestamp': filters.date(localtime(catalogue.timestamp), 'Y-m-d H:i:s')
             }
        )
    return HttpResponse(json.dumps(data, indent=2), content_type='application/json')


@login_required
def catalogue_history_fetch(request, certname=None, catalogue_hash=None):
    data = dict()
    show = request.GET.get('show', None)
    try:
        catalogue = SavedCatalogs.objects.get(hostname=certname, catalogue_id=catalogue_hash)
        data['catalogue'] = {
            'hostname': catalogue.hostname,
            'catalogue_id': catalogue.catalogue_id,
            'linked_report': catalogue.linked_report,
            'catalogue_timestamp': filters.date(localtime(catalogue.timestamp), 'Y-m-d H:i:s'),
        }
        if show == 'edges':
            data['data'] = json.loads(catalogue.catalogue)['edges']['data']
        elif show == 'resources':
            data['data'] = json.loads(catalogue.catalogue)['resources']['data']
        else:
            data['data'] = json.loads(catalogue.catalogue)

    except SavedCatalogs.DoesNotExist:
        data['error'] = "Could not find catalogue with specfied certname and report hash."
        data['certname'] = certname
        data['linked_report'] = catalogue_hash
        return HttpResponseBadRequest(json.dumps(data, indent=2), 'application/json')
    return HttpResponse(json.dumps(data, indent=2), 'application/json')

