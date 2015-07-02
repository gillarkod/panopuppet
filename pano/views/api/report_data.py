__author__ = 'etaklar'
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse
from django.views.decorators.cache import cache_page
from pano.methods.dictfuncs import sort_table as sort_tables
from pano.puppetdb import puppetdb
from pano.settings import CACHE_TIME
from pano.puppetdb.puppetdb import get_server
import json
from django.template import defaultfilters as filters
from django.utils.timezone import localtime
from pano.puppetdb.pdbutils import json_to_datetime


@login_required
@cache_page(CACHE_TIME)
def reports_json(request, certname=None):
    source_url, source_certs, source_verify = get_server(request)
    # Redirects to the events page if GET param latest is true..
    context = {}
    page_num = int(request.GET.get('page', 0))
    if page_num <= 0:
        offset = 0
    else:
        offset = "{:.0f}".format(page_num * 25)

    reports_params = {
        'query':
            {
                1: '["=","certname","' + certname + '"]'
            },
        'order-by':
            {
                'order-field':
                    {
                        'field': 'start-time',
                        'order': 'desc',
                    },
                'query-field': {'field': 'certname'},
            },
        'limit': 25,
        'include-total': 'true',
        'offset': offset,
    }
    reports_list, headers = puppetdb.api_get(
        api_url=source_url,
        cert=source_certs,
        verify=source_verify,
        path='/reports',
        api_version='v4',
        params=puppetdb.mk_puppetdb_query(
            reports_params),
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
            'summarize-by': 'certname',
        }
        eventcount_list = puppetdb.api_get(
            path='event-counts',
            api_url=source_url,
            api_version='v4',
            params=puppetdb.mk_puppetdb_query(events_params),
        )
        # Make list of the results
        for event in eventcount_list:
            if event['subject']['title'] == report['certname']:
                found_report = True
                report_status.append({
                    'hash': report['hash'],
                    'certname': report['certname'],
                    'environment': report['environment'],
                    'start_time': filters.date(localtime(json_to_datetime(report['start-time'])), 'Y-m-d H:i:s'),
                    'end_time': filters.date(localtime(json_to_datetime(report['start-time'])), 'Y-m-d H:i:s'),
                    'events_successes': event['successes'],
                    'events_noops': event['noops'],
                    'events_failures': event['failures'],
                    'events_skipped': event['skips'],
                    'report_status': report['status'],
                    'config_version': report['configuration-version']
                })
                break
        if found_report is False:
                report_status.append({
                    'hash': report['hash'],
                    'certname': report['certname'],
                    'environment': report['environment'],
                    'start_time': filters.date(localtime(json_to_datetime(report['start-time'])), 'Y-m-d H:i:s'),
                    'end_time': filters.date(localtime(json_to_datetime(report['start-time'])), 'Y-m-d H:i:s'),
                    'events_successes': 0,
                    'events_noops': 0,
                    'events_failures': 0,
                    'events_skipped': 0,
                    'report_status': 0,
                    'config_version': report['configuration-version']
                })

    context['certname'] = certname
    context['reports'] = report_status
    context['curr_page'] = page_num
    context['tot_pages'] = "{:.0f}".format(num_pages)
    return HttpResponse(json.dumps(context), content_type="application/json")
