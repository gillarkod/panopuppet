from django.shortcuts import redirect, render
from django.http import HttpResponseBadRequest, HttpResponseRedirect
import pytz
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from pano.puppetdb import puppetdb
from pano.methods.dictfuncs import dictstatus as dictstatus


# Caching for certain views.
from django.views.decorators.cache import cache_page
from pano.settings import CACHE_TIME

# Dashboard functions
from pano.puppetdb.pdbutils import run_puppetdb_jobs, json_to_datetime


def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/pano/dashboard")


def splash(request):
    if request.method == 'POST':
        if 'timezone' in request.POST:
            request.session['django_timezone'] = request.POST['timezone']
            return redirect(request.POST['url'])
        elif 'username' in request.POST and 'password' in request.POST:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            next_url = False
            if 'nexturl' in request.POST:
                next_url = request.POST['nexturl']
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if next_url:
                        return redirect(next_url)
                    else:
                        return redirect('dashboard')
                else:
                    context = {'timezones': pytz.common_timezones,
                               'login_error': "Account is disabled.",
                               'nexturl': next_url}
                    return render(request, 'pano/splash.html', context)
            else:
                # Return an 'invalid login' error message.
                context = {'timezones': pytz.common_timezones,
                           'login_error': "Invalid credentials",
                           'nexturl': next_url}
                return render(request, 'pano/splash.html', context)
        return redirect('dashboard')
    else:
        user = request.user.username
        context = {'timezones': pytz.common_timezones,
                   'username': user}
        return render(request, 'pano/splash.html', context)


@login_required
@cache_page(CACHE_TIME)
def index(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['url'])
    else:

        events_params = {
            'query':
                {
                    1: '["=","latest-report?",true]'
                },
            'summarize-by': 'certname',
        }
        nodes_params = {
            'limit': 25,
            'order-by': {
                'order-field': {
                    'field': 'report-timestamp',
                    'order': 'desc',
                },
                'query-field': {'field': 'name'},
            },
        }

        jobs = {
            'population': {
                'id': 'population',
                'path': '/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=num-nodes',
                'verify': False,
            },
            'tot_resource': {
                'id': 'tot_resource',
                'path': '/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=num-resources',
                'verify': False,
            },
            'avg_resource': {
                'id': 'avg_resource',
                'path': '/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=avg-resources-per-node',
                'verify': False,
            },
            'all_nodes': {
                'id': 'all_nodes',
                'path': '/nodes',
                'verify': False,
            },
            'events': {
                'id': 'event-counts',
                'path': 'event-counts',
                'params': events_params,
                'verify': False,
            },
            'nodes': {
                'id': 'nodes',
                'path': '/nodes',
                'params': nodes_params,
                'verify': False,
            },
        }
        results = run_puppetdb_jobs(jobs)

        # Dashboard to show nodes of "recent, failed, unreported or changed"
        dashboard_show = request.GET.get('show', 'recent')

        # Assign vars from the completed jobs
        puppet_population = results['population']
        # Total resources managed by puppet metric
        total_resources = results['tot_resource']
        # Average resource per node metric
        avg_resource_node = results['avg_resource']
        # Information about all active nodes in puppet
        all_nodes_list = results['all_nodes']
        # All available events for the latest puppet reports
        event_list = results['event-counts']
        node_list = results['nodes']

        unreported_list = dictstatus(
            all_nodes_list, event_list, sort=True, get_status="unreported")
        failed_list = dictstatus(
            all_nodes_list, event_list, sort=True, get_status="failed")
        changed_list = dictstatus(
            all_nodes_list, event_list, sort=True, get_status="changed")

        changed_list = [x for x in changed_list if x not in unreported_list and x not in failed_list]
        failed_list = [x for x in failed_list if x not in unreported_list]
        if dashboard_show == 'recent':
            merged_nodes_list = dictstatus(
                node_list, event_list, sort=False, get_status="all")
        elif dashboard_show == 'failed':
            merged_nodes_list = failed_list
        elif dashboard_show == 'unreported':
            merged_nodes_list = unreported_list
        elif dashboard_show == 'changed':
            merged_nodes_list = changed_list
        else:
            merged_nodes_list = dictstatus(
                node_list, event_list, sort=False, get_status="all")

        node_unreported_count = len(unreported_list)
        node_fail_count = len(failed_list)
        node_change_count = len(changed_list)

        context = {'node_list': merged_nodes_list,
                   'certname': certname,
                   'show_nodes': dashboard_show,
                   'timezones': pytz.common_timezones,
                   'population': puppet_population['Value'],
                   'total_resource': total_resources['Value'],
                   'avg_resource': "{:.2f}".format(avg_resource_node['Value']),
                   'failed_nodes': node_fail_count,
                   'changed_nodes': node_change_count,
                   'unreported_nodes': node_unreported_count,
                   }

        return render(request, 'pano/index.html', context)


@login_required
@cache_page(CACHE_TIME)
def nodes(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
        try:
            limits = int(request.GET.get('limits', 50))
            if limits <= 0:
                limits = 50
        except:
            return HttpResponseBadRequest('Oh no! Your filters were invalid.')

        page_num = int(request.GET.get('page', 0))
        if page_num <= 0:
            offset = 0
        else:
            offset = "{:.0f}".format(page_num * limits)
        try:
            sort_field = str(request.GET.get('sortfield', 'latestReport'))
        except:
            return HttpResponseBadRequest('Oh no! Your filters were invalid.')
        try:
            sort_field_order = str(request.GET.get('sortfieldby', 'desc'))
        except:
            return HttpResponseBadRequest('Oh no! Your filters were invalid.')

        search_node = request.GET.get('search', None)
        if search_node is not None:
            node_params = {
                'query':
                    {
                        1: '["~","name","' + search_node + '"]'
                    },
                'limit': limits,
                'include-total': 'true',
                'offset': offset,
            }
        else:
            node_params = {
                'query': {},
                'limit': limits,
                'include-total': 'true',
                'offset': offset,
            }

        node_list, headers = puppetdb.api_get(path='/nodes',
                                              params=puppetdb.mk_puppetdb_query(
                                                  node_params),
                                              verify=False)
        # Work out the number of pages from the xrecords response
        xrecords = headers['X-Records']
        num_pages_wdec = float(xrecords) / limits
        num_pages_wodec = float("{:.0f}".format(num_pages_wdec))
        if num_pages_wdec > num_pages_wodec:
            num_pages = num_pages_wodec + 1
        else:
            num_pages = num_pages_wodec

        # return fields that you can sort by
        valid_sort_fields = (
            'certname',
            'latestCatalog',
            'latestReport',
            'latestFacts',
            'success',
            'noop',
            'failure',
            'skipped')

        # for each node in the node_list, find out if the latest run has any failures
        # v3/event-counts --data-urlencode query='["=","latest-report?",true]'
        # --data-urlencode summarize-by='certname'
        report_params = {
            'query':
                {
                    1: '["=","latest-report?",true]'
                },
            'summarize-by': 'certname',
        }
        report_list = puppetdb.api_get(path='event-counts',
                                       params=puppetdb.mk_puppetdb_query(
                                           report_params),
                                       verify=False)
        if sort_field_order == 'desc':
            merged_list = dictstatus(
                node_list, report_list, sortby=sort_field, asc=True)
            sort_field_order_opposite = 'asc'
        else:
            merged_list = dictstatus(
                node_list, report_list, sortby=sort_field, asc=False)
            sort_field_order_opposite = 'desc'

        """
        c_r_s* = current request sort
        c_r_* = current req
        r_s* = requests available
        """
        context = {
            'node_list': merged_list,
            'q_certname': certname,
            'timezones': pytz.common_timezones,
            'c_r_limit': request.GET.get('limits', 50),
            'r_sfield': valid_sort_fields,
            'c_r_sfield': sort_field,
            'r_sfieldby': ['asc', 'desc'],
            'c_r_sfieldby': sort_field_order,
            'c_r_sfieldby_o': sort_field_order_opposite,
            'curr_page': page_num,
            'tot_pages': "{:.0f}".format(num_pages),
        }
        return render(request, 'pano/nodes.html', context)


@login_required
@cache_page(CACHE_TIME)
def reports(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

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
            latest_report = puppetdb.api_get(path='/reports',
                                             api_version='v4',
                                             params=puppetdb.mk_puppetdb_query(
                                                 latest_report_params),
                                             verify=False)
            report_hash = ""
            for report in latest_report:
                report_hash = report['hash']
            return redirect('/pano/events/' + certname + '/' + report_hash + '?report_timestamp=' + request.GET.get('report_timestamp'))

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
    reports_list, headers = puppetdb.api_get(path='/reports',
                                             api_version='v4',
                                             params=puppetdb.mk_puppetdb_query(
                                                 reports_params),
                                             verify=False)

    # Work out the number of pages from the xrecords response
    xrecords = headers['X-Records']
    num_pages_wdec = float(xrecords) / 25
    num_pages_wodec = float("{:.0f}".format(num_pages_wdec))
    if num_pages_wdec > num_pages_wodec:
        num_pages = num_pages_wodec + 1
    else:
        num_pages = num_pages_wodec

    report_status = {}
    for report in reports_list:
        events_params = {
            'query':
                {
                    1: '["=","report","' + report['hash'] + '"]'
                },
            'summarize-by': 'certname',
        }
        eventcount_list = puppetdb.api_get(path='event-counts',
                                           params=puppetdb.mk_puppetdb_query(
                                               events_params),
                                           verify=False)
        for event in eventcount_list:
            if event['subject']['title'] == report['certname']:
                report_status[report['hash']] = {
                    'failure': event['failures'],
                    'success': event['successes'],
                    'noop': event['noops'],
                    'skipped': event['skips'],
                }

    context = {
        'timezones': pytz.common_timezones,
        'certname': certname,
        'reports': reports_list,
        'report_status': report_status,
        'curr_page': page_num,
        'tot_pages': "{:.0f}".format(num_pages),
    }

    return render(request, 'pano/reports.html', context)


@login_required
def analytics(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
        events_class_params = {
            'query':
                {
                    1: '["=","latest-report?",true]'
                },
            'summarize-by': 'containing-class',
        }
        events_resource_params = {
            'query':
                {
                    1: '["=","latest-report?",true]'
                },
            'summarize-by': 'resource',
        }
        events_status_params = {
            'query':
                {
                    1: '["=","latest-report?",true]'
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
                'params': events_class_params,
                'verify': False,
            },
            'events_resource_list': {
                'id': 'events_resource_list',
                'path': '/event-counts',
                'params': events_resource_params,
                'verify': False,
            },
            'events_status_list': {
                'id': 'events_status_list',
                'path': '/aggregate-event-counts',
                'params': events_status_params,
                'verify': False,
            },
            'reports_run_avg': {
                'id': 'reports_run_avg',
                'path': '/reports',
                'params': reports_runavg_params,
                'verify': False,
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

        return render(request, 'pano/analytics.html', context)


@login_required
@cache_page(CACHE_TIME)
def detailed_events(request, certname=None, hashid=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
        report_timestamp = request.GET.get('report_timestamp')
        events_params = {
            'query':
                {
                    1: '["=","report","' + hashid + '"]'
                },
            'order-by':
                {
                    'order-field':
                        {
                            'field': 'containing-class',
                            'order': 'asc',
                        },
                    'query-field': {'field': 'certname'},
                },
        }
        events_list = puppetdb.api_get(path='/events',
                                       params=puppetdb.mk_puppetdb_query(
                                           events_params),
                                       verify=False)

        context = {
            'timezones': pytz.common_timezones,
            'certname': certname,
            'report_timestamp': report_timestamp,
            'hashid': hashid,
            'events_list': events_list,
        }

        return render(request, 'pano/detailed_events.html', context)


@login_required
@cache_page(CACHE_TIME)
def facts(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
        facts_params = {
            'query':
                {
                    1: '["=","certname","' + certname + '"]'
                },
        }
        facts_list = puppetdb.api_get(path='/facts/',
                                      params=puppetdb.mk_puppetdb_query(
                                          facts_params),
                                      verify=False)
        context = {
            'timezones': pytz.common_timezones,
            'certname': certname,
            'facts_list': facts_list,
        }

        return render(request, 'pano/facts.html', context)
