from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page
import pytz
from pano.puppetdb.pdbutils import run_puppetdb_jobs, json_to_datetime
from pano.settings import CACHE_TIME

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def analytics(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
        events_class_params = {
            'query':
                {
                    1: '["and",["=","latest-report?",true],["in", "certname",["extract", "certname",["select-nodes",["null?","deactivated",true]]]]]'
                },
            'summarize-by': 'containing-class',
        }
        events_resource_params = {
            'query':
                {
                    1: '["and",["=","latest-report?",true],["in", "certname",["extract", "certname",["select-nodes",["null?","deactivated",true]]]]]'
                },
            'summarize-by': 'resource',
        }
        events_status_params = {
            'query':
                {
                    1: '["and",["=","latest-report?",true],["in", "certname",["extract", "certname",["select-nodes",["null?","deactivated",true]]]]]'
                },
            'summarize-by': 'resource',
        }
        reports_runavg_params = {
            'limit': 100,
            'order-by': {
                'order-field': {
                    'field': 'receive-time',
                    'order': 'desc',
                },
                'query-field': {'field': 'certname'},
            },
        }
        jobs = {
            'events_class_list': {
                'id': 'events_class_list',
                'path': '/event-counts',
                'api_version': 'v4',
                'params': events_class_params,
            },
            'events_resource_list': {
                'id': 'events_resource_list',
                'path': '/event-counts',
                'api_version': 'v4',
                'params': events_resource_params,
            },
            'events_status_list': {
                'id': 'events_status_list',
                'path': '/aggregate-event-counts',
                'api_version': 'v4',
                'params': events_status_params,
            },
            'reports_run_avg': {
                'id': 'reports_run_avg',
                'path': '/reports',
                'params': reports_runavg_params,
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
                (json_to_datetime(report['end-time']) - json_to_datetime(report['start-time'])).total_seconds())
            avg_run_time += int(run_time)
            run_avg_times.append(run_time)
        avg_run_time = "{0:.0f}".format(avg_run_time / num_runs_avg)

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

        for status, value in events_status_list.items():
            if value is 0 or status == 'total':
                continue
            class_status_results.append((status, value))

        context = {
            'timezones': pytz.common_timezones,
            'class_events': class_event_results,
            'class_status': class_status_results,
            'resource_events': class_resource_results,
            'run_times': run_avg_times,
            'run_num': num_runs_avg,
            'run_avg': avg_run_time,
        }

        return render(request, 'pano/analytics/analytics.html', context)
