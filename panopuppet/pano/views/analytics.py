import pytz

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page

from pano.puppetdb.pdbutils import run_puppetdb_jobs, json_to_datetime
from pano.puppetdb.puppetdb import set_server, get_server
from pano.settings import AVAILABLE_SOURCES, CACHE_TIME

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def analytics(request):
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
    events_class_params = {
        'query':
            {
                1: '["and",["=","latest_report?",true],["in","certname",["extract","certname",["select_nodes",["null?","deactivated",true]]]]]'
            },
        'summarize_by': 'containing_class',
    }
    events_resource_params = {
        'query':
            {
                1: '["and",["=","latest_report?",true],["in","certname",["extract","certname",["select_nodes",["null?","deactivated",true]]]]]'
            },
        'summarize_by': 'resource',
    }
    events_status_params = {
        'query':
            {
                1: '["and",["=","latest_report?",true],["in","certname",["extract","certname",["select_nodes",["null?","deactivated",true]]]]]'
            },
        'summarize_by': 'resource',
    }
    reports_runavg_params = {
        'limit': 100,
        'order_by': {
            'order_field': {
                'field': 'receive_time',
                'order': 'desc',
            },
            'query_field': {'field': 'certname'},
        },
    }
    jobs = {
        'events_class_list': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'events_class_list',
            'path': '/event-counts',
            'api_version': 'v4',
            'params': events_class_params,
            'request': request
        },
        'events_resource_list': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'events_resource_list',
            'path': '/event-counts',
            'api_version': 'v4',
            'params': events_resource_params,
            'request': request
        },
        'events_status_list': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'events_status_list',
            'path': '/aggregate-event-counts',
            'api_version': 'v4',
            'params': events_status_params,
            'request': request
        },
        'reports_run_avg': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'reports_run_avg',
            'path': '/reports',
            'api_version': 'v4',
            'params': reports_runavg_params,
            'request': request
        },
    }

    job_results = run_puppetdb_jobs(jobs, 4)

    reports_run_avg = job_results['reports_run_avg']
    events_class_list = job_results['events_class_list']
    events_resource_list = job_results['events_resource_list']
    events_status_list = job_results['events_status_list']

    num_runs_avg = len(reports_run_avg)
    run_avg_times = []
    avg_run_time = 0
    for report in reports_run_avg:
        run_time = "{0:.0f}".format(
            (json_to_datetime(report['end_time']) - json_to_datetime(report['start_time'])).total_seconds())
        avg_run_time += int(run_time)
        run_avg_times.append(run_time)
    if num_runs_avg != 0:
        avg_run_time = "{0:.0f}".format(avg_run_time / num_runs_avg)
    else:
        avg_run_time = 0

    class_event_results = []
    class_resource_results = []
    class_status_results = []

    for item in events_class_list:
        class_name = item['subject']['title']
        class_total = item['skips'] + item['failures'] + item['noops'] + item['successes']
        class_event_results.append((class_name, class_total))

    for item in events_resource_list:
        class_name = item['subject']['type']
        class_total = item['skips'] + item['failures'] + item['noops'] + item['successes']
        class_resource_results.append((class_name, class_total))
    print(events_status_list)
    if events_status_list:
        for status, value in events_status_list[0].items():
            print(status, value)
            if value is 0 or status == 'total' or status == 'summarize_by':
                continue
            class_status_results.append((status, value))

    context['class_events'] = class_event_results
    context['class_status'] = class_status_results
    context['resource_events'] = class_resource_results
    context['run_times'] = run_avg_times
    context['run_num'] = num_runs_avg
    context['run_avg'] = avg_run_time

    return render(request, 'pano/analytics/analytics.html', context)
