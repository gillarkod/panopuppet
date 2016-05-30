import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse
from django.template import defaultfilters as filters
from django.utils.timezone import localtime
from django.views.decorators.cache import cache_page

from panopuppet.pano.puppetdb import puppetdb
from panopuppet.pano.puppetdb.pdbutils import json_to_datetime
from panopuppet.pano.puppetdb.puppetdb import get_server
from panopuppet.pano.settings import CACHE_TIME

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def reports_json(request, certname=None):
    source_url, source_certs, source_verify = get_server(request)
    # Redirects to the events page if GET param latest is true..
    context = {}
    # Cur Page Number
    if request.GET.get('page', False):
        if request.session['report_page'] != int(request.GET.get('page', 1)):
            request.session['report_page'] = int(request.GET.get('page', 1))
        if request.session['report_page'] <= 0:
            request.session['report_page'] = 1
    else:
        if 'report_page' not in request.session:
            request.session['report_page'] = 1
    if request.session['report_page'] <= 0:
        offset = 0
    else:
        offset = (25 * request.session['report_page']) - 25
    reports_params = {
        'query':
            {
                1: '["=","certname","' + certname + '"]'
            },
        'order_by':
            {
                'order_field':
                    {
                        'field': 'start_time',
                        'order': 'desc',
                    },
            },
        'limit': 25,
        'include_total': 'true',
        'offset': offset,
    }
    reports_list, headers = puppetdb.api_get(
        api_url=source_url,
        cert=source_certs,
        verify=source_verify,
        path='/reports',
        api_version='v4',
        params=puppetdb.mk_puppetdb_query(
            reports_params, request),
    )
    # Work out the number of pages from the xrecords response
    xrecords = headers['X-Records']
    num_pages_wdec = float(xrecords) / 25
    num_pages_wodec = float("{:.0f}".format(num_pages_wdec))
    if num_pages_wdec > num_pages_wodec:
        num_pages = num_pages_wodec + 1
    else:
        num_pages = num_pages_wodec

    report_status = []
    for report in reports_list:
        found_report = False
        events_params = {
            'query':
                {
                    1: '["=","report","' + report['hash'] + '"]'
                },
            'summarize_by': 'certname',
        }
        eventcount_list = puppetdb.api_get(
            path='event-counts',
            api_url=source_url,
            api_version='v4',
            verify=source_verify,
            cert=source_certs,
            params=puppetdb.mk_puppetdb_query(events_params, request),
        )
        # Make list of the results
        for event in eventcount_list:
            if event['subject']['title'] == report['certname']:
                found_report = True
                report_status.append({
                    'hash': report['hash'],
                    'certname': report['certname'],
                    'environment': report['environment'],
                    'is_noop': report['noop'],
                    'start_time': filters.date(localtime(json_to_datetime(report['start_time'])), 'Y-m-d H:i:s'),
                    'end_time': filters.date(localtime(json_to_datetime(report['end_time'])), 'Y-m-d H:i:s'),
                    'events_successes': event['successes'],
                    'events_noops': event['noops'],
                    'events_failures': event['failures'],
                    'events_skipped': event['skips'],
                    'report_status': report['status'],
                    'config_version': report['configuration_version'],
                    'run_duration': "{0:.0f}".format(
                        (json_to_datetime(report['end_time']) - json_to_datetime(report['start_time'])).total_seconds())
                })
                break
        if found_report is False:
            report_status.append({
                'hash': report['hash'],
                'certname': report['certname'],
                'environment': report['environment'],
                'is_noop': report['noop'],
                'start_time': filters.date(localtime(json_to_datetime(report['start_time'])), 'Y-m-d H:i:s'),
                'end_time': filters.date(localtime(json_to_datetime(report['end_time'])), 'Y-m-d H:i:s'),
                'events_successes': 0,
                'events_noops': 0,
                'events_failures': 0,
                'events_skipped': 0,
                'report_status': report['status'],
                'config_version': report['configuration_version'],
                'run_duration': "{0:.0f}".format(
                    (json_to_datetime(report['end_time']) - json_to_datetime(report['start_time'])).total_seconds())
            })

    context['certname'] = certname
    context['reports_list'] = report_status
    context['curr_page'] = request.session['report_page']
    context['tot_pages'] = "{:.0f}".format(num_pages)
    return HttpResponse(json.dumps(context, indent=2), content_type="application/json")


def reports_search_json(request):
    context = dict()
    if request.method == 'GET':
        if 'search' in request.GET:
            search = request.GET.get('search')
        if 'certname' in request.GET:
            certname = request.GET.get('certname')
        if not certname or not search:
            context['error'] = 'Must specify both certname and search query.'
            return HttpResponse(json.dumps(context, indent=2), content_type="application/json")
    source_url, source_certs, source_verify = get_server(request)
    # Redirects to the events page if GET param latest is true..
    reports_params = {
        'query':
            {
                'operator': 'and',
                1: '["=","certname","' + certname + '"]',
                2: '["~","hash","^' + search + '"]'
            },
        'order_by':
            {
                'order_field':
                    {
                        'field': 'start_time',
                        'order': 'desc',
                    },
            }
    }

    reports_list = puppetdb.api_get(
        path='/reports',
        api_url=source_url,
        api_version='v4',
        params=puppetdb.mk_puppetdb_query(reports_params, request),
    )
    return HttpResponse(json.dumps(reports_list, indent=2), content_type="application/json")
