from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page
from pano.methods.dictfuncs import sort_table as sort_tables
from pano.puppetdb import puppetdb
from pano.settings import CACHE_TIME
from pano.puppetdb.puppetdb import set_server, get_server
from pano.settings import AVAILABLE_SOURCES, NODES_DEFAULT_FACTS
import pytz
from pano.puppetdb.pdbutils import json_to_datetime
from django.template import defaultfilters as filters
from django.utils.timezone import localtime

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def reports(request, certname=None):
    context = {'timezones': pytz.common_timezones,
               'SOURCES': AVAILABLE_SOURCES}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    source_url, source_certs, source_verify = get_server(request)
    # Redirects to the events page if GET param latest is true..
    if request.GET.get('latest', False):
        if request.GET.get('latest') == "true":
            latest_report_params = {
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
                'limit': 1,
            }
            latest_report = puppetdb.api_get(
                api_url=source_url,
                cert=source_certs,
                verify=source_verify,
                path='/reports',
                api_version='v4',
                params=puppetdb.mk_puppetdb_query(latest_report_params),
            )
            report_hash = ""
            for report in latest_report:
                report_env = report['environment']
                report_hash = report['hash']
            return redirect('/pano/events/' + report_hash + '?report_timestamp=' + request.GET.get(
                'report_timestamp') + '&envname=' + report_env)

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
                # hashid, certname, environment, time start, time end, success, noop, failure, pending
                report_status.append(
                    [report['hash'],
                     report['certname'],
                     report['environment'],
                     report['start-time'],
                     report['end-time'],
                     event['successes'],
                     event['noops'],
                     event['failures'],
                     event['skips'],
                     report['status'],
                     report['configuration-version']])
                break
        if found_report is False:
            report_status.append(
                [report['hash'],
                 report['certname'],
                 report['environment'],
                 report['start-time'],
                 report['end-time'],
                 0,
                 0,
                 0,
                 0,
                 report['status'],
                 report['configuration-version']])

    report_status = sort_tables(report_status, order=True, col=3)

    # Get runtimes for the latest (25) runs.
    report_runtimes = []
    for report in report_status:
        run_time = "{0:.0f}".format(
            (json_to_datetime(report[4]) - json_to_datetime(report[3])).total_seconds())
        report_timestamp = filters.date(localtime(json_to_datetime(report[3])), 'Y-m-d H:i:s')
        report_runtimes.append([run_time, report_timestamp])

    context['certname'] = certname
    context['reports'] = report_status
    context['report_runtimes'] = report_runtimes
    context['curr_page'] = page_num
    context['node_facts'] = ','.join(NODES_DEFAULT_FACTS)
    context['tot_pages'] = "{:.0f}".format(num_pages)

    return render(request, 'pano/reports.html', context)
