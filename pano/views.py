from django.shortcuts import redirect, render
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.cache import cache_page
import pytz
import datetime

from pano.puppetdb import puppetdb
from pano.methods.dictfuncs import dictstatus as dictstatus
from pano.methods.dictfuncs import sort_table as sort_tables
from pano.settings import CACHE_TIME
from pano.puppetdb.pdbutils import run_puppetdb_jobs, json_to_datetime
from pano.methods.filebucket import get_file as get_filebucket
from pano.methods import events
import csv
from django.http import StreamingHttpResponse


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


class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


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
                    1: '["and",["=","latest-report?",true],["in", "certname",["extract", "certname",["select-nodes",["null?","deactivated",true]]]]]'
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
                'query-field': {'field': 'certname'},
            },
        }

        jobs = {
            'population': {
                'id': 'population',
                'path': '/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=num-nodes',
            },
            'tot_resource': {
                'id': 'tot_resource',
                'path': '/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=num-resources',
            },
            'avg_resource': {
                'id': 'avg_resource',
                'path': '/metrics/mbean/com.puppetlabs.puppetdb.query.population:type=default,name=avg-resources-per-node',
            },
            'all_nodes': {
                'api_version': 'v4',
                'id': 'all_nodes',
                'path': '/nodes',
            },
            'events': {
                'id': 'event-counts',
                'path': 'event-counts',
                'api_version': 'v4',
                'params': events_params,
            },
            'nodes': {
                'api_version': 'v4',
                'id': 'nodes',
                'path': '/nodes',
                'params': nodes_params,
            },
        }
        puppetdb_results = run_puppetdb_jobs(jobs)
        # Dashboard to show nodes of "recent, failed, unreported or changed"
        dashboard_show = request.GET.get('show', 'recent')

        # Assign vars from the completed jobs
        puppet_population = puppetdb_results['population']
        # Total resources managed by puppet metric
        total_resources = puppetdb_results['tot_resource']
        # Average resource per node metric
        avg_resource_node = puppetdb_results['avg_resource']
        # Information about all active nodes in puppet
        all_nodes_list = puppetdb_results['all_nodes']
        # All available events for the latest puppet reports
        event_list = puppetdb_results['event-counts']
        node_list = puppetdb_results['nodes']

        failed_list, changed_list, unreported_list, mismatch_list, pending_list = dictstatus(all_nodes_list,
                                                                                             event_list,
                                                                                             sort=True,
                                                                                             sortby='latestReport',
                                                                                             get_status='notall')
        pending_list = [x for x in pending_list if x not in unreported_list]
        changed_list = [x for x in changed_list if
                        x not in unreported_list and x not in failed_list and x not in pending_list]
        failed_list = [x for x in failed_list if x not in unreported_list]
        unreported_list = [x for x in unreported_list if x not in failed_list]

        if dashboard_show == 'recent':
            merged_nodes_list = dictstatus(
                node_list, event_list, sort=False, get_status="all")
        elif dashboard_show == 'failed':
            merged_nodes_list = failed_list
        elif dashboard_show == 'unreported':
            merged_nodes_list = unreported_list
        elif dashboard_show == 'changed':
            merged_nodes_list = changed_list
        elif dashboard_show == 'failed_catalogs':
            merged_nodes_list = mismatch_list
        elif dashboard_show == 'pending':
            merged_nodes_list = pending_list
        else:
            merged_nodes_list = dictstatus(
                node_list, event_list, sort=False, get_status="all")

        node_unreported_count = len(unreported_list)
        node_fail_count = len(failed_list)
        node_change_count = len(changed_list)
        node_off_timestamps_count = len(mismatch_list)
        node_pending_count = len(pending_list)

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
                   'weird_timestamps': node_off_timestamps_count,
                   'pending_nodes': node_pending_count,
                   }
        return render(request, 'pano/index.html', context)


@login_required
@cache_page(CACHE_TIME)
def nodes(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
        try:
            limits = int(request.GET.get('limits', 50))
            if limits <= 0:
                limits = 50
            sort_field = str(request.GET.get('sortfield', 'latestReport'))
            sort_field_order = str(request.GET.get('sortfieldby', 'desc'))
            page_num = int(request.GET.get('page', 1))
            # Search parameters takes a valid puppetdb query string
            search_node = request.GET.get('search', None)
            # If user requested to download csv formatted file. Default value is False
            dl_csv = request.GET.get('dl_csv', False)
            if dl_csv == 'true':
                dl_csv = True
            else:
                dl_csv = False
        except:
            return HttpResponseBadRequest('Oh no! Your filters were invalid.')

        if search_node is not None:
            node_params = {
                'query':
                    {
                        1: search_node
                    },
            }
        else:
            node_params = {
                'query': {},
            }

        node_list = puppetdb.api_get(path='/nodes',
                                     api_version='v4',
                                     params=puppetdb.mk_puppetdb_query(
                                         node_params),
                                     )
        # Work out the number of pages from the xrecords response
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
                    1: '["and",["=","latest-report?",true],["in", "certname",["extract", "certname",["select-nodes",["null?","deactivated",true]]]]]'
                },
            'summarize-by': 'certname',
        }
        report_list = puppetdb.api_get(path='event-counts',
                                       params=puppetdb.mk_puppetdb_query(
                                           report_params),
                                       )
        if sort_field_order == 'desc':
            merged_list = dictstatus(
                node_list, report_list, sortby=sort_field, asc=True)
            sort_field_order_opposite = 'asc'
        else:
            merged_list = dictstatus(
                node_list, report_list, sortby=sort_field, asc=False)
            sort_field_order_opposite = 'desc'

        if dl_csv is True:
            if merged_list == []:
                pass
            else:
                # Generate a sequence of rows. The range is based on the maximum number of
                # rows that can be handled by a single sheet in most spreadsheet
                # applications.
                csv_headers = ('Certname',
                               'Latest Catalog',
                               'Latest Report',
                               'Latest Facts',
                               'Success',
                               'Noop',
                               'Failure',
                               'Skipped')

                merged_list.insert(0, csv_headers)
                rows = merged_list
                pseudo_buffer = Echo()
                writer = csv.writer(pseudo_buffer)
                response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                                 content_type="text/csv")
                response['Content-Disposition'] = 'attachment; filename="puppetdata-%s.csv"' % (datetime.datetime.now())
                return response
        paginator = Paginator(merged_list, limits)

        try:
            merged_list = paginator.page(page_num)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            merged_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page
            merged_list = paginator.page(paginator.num_pages)

        """
        c_r_s* = current request sort
        c_r_* = current req
        r_s* = requests available
        """
        context = {
            'node_list': merged_list,
            'timezones': pytz.common_timezones,
            'c_r_limit': request.GET.get('limits', 50),
            'r_sfield': valid_sort_fields,
            'c_r_sfield': sort_field,
            'r_sfieldby': ['asc', 'desc'],
            'c_r_sfieldby': sort_field_order,
            'c_r_sfieldby_o': sort_field_order_opposite,
            'tot_pages': paginator.page_range,
        }
        return render(request, 'pano/nodes.html', context)


@login_required
@cache_page(CACHE_TIME)
def reports(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

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
            latest_report = puppetdb.api_get(path='/reports',
                                             api_version='v4',
                                             params=puppetdb.mk_puppetdb_query(
                                                 latest_report_params),
                                             )
            report_hash = ""
            for report in latest_report:
                report_env = report['environment']
                report_hash = report['hash']
            return redirect('/pano/events/' + certname + '/' + report_hash + '?report_timestamp=' + request.GET.get(
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
    reports_list, headers = puppetdb.api_get(path='/reports',
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
        eventcount_list = puppetdb.api_get(path='event-counts',
                                           api_version='v4',
                                           params=puppetdb.mk_puppetdb_query(
                                               events_params),
                                           )
        # Make list of the results
        for event in eventcount_list:
            if event['subject']['title'] == report['certname']:
                found_report = True
                # hashid, certname, environment, time start, time end, success, noop, failure, pending
                report_status.append([report['hash'], report['certname'], report['environment'], report['start-time'],
                                      report['end-time'],
                                      event['successes'], event['noops'], event['failures'], event['skips']])
                break
        if found_report is False:
            report_status.append(
                [report['hash'], report['certname'], report['environment'], report['start-time'], report['end-time'],
                 0, 0, 0, 0])
    report_status = sort_tables(report_status, order=True, col=3)
    context = {
        'timezones': pytz.common_timezones,
        'certname': certname,
        'reports': report_status,
        'curr_page': page_num,
        'tot_pages': "{:.0f}".format(num_pages),
    }

    return render(request, 'pano/reports.html', context)


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


@login_required
@cache_page(CACHE_TIME * 60)  # Cache for cache_time multiplied 60 because the report will never change...
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
                            'field': 'timestamp',
                            'order': 'asc',
                        },
                    'query-field': {'field': 'certname'},
                },
        }
        events_list = puppetdb.api_get(path='/events',
                                       api_version='v4',
                                       params=puppetdb.mk_puppetdb_query(
                                           events_params),
                                       )
        single_event = ''
        environment = ''

        event_execution_times = []
        sorted_events = None
        last_event_time = None
        last_event_title = None
        run_end_time = None

        if len(events_list) != 0:
            single_event = events_list[0]
            environment = single_event['environment']
            for event in events_list:
                event_title = event['resource-title']
                event_start_time = json_to_datetime(event['timestamp'])
                if last_event_time is None and last_event_title is None:
                    last_event_time = event_start_time
                    last_event_title = event_title
                    run_end_time = json_to_datetime(event['run-end-time'])
                    continue
                else:
                    event_exec_time = (event_start_time - last_event_time).total_seconds()
                    add_event = (last_event_title, event_exec_time)
                    event_execution_times.append(add_event)
                    last_event_time = event_start_time
                    last_event_title = event_title
            event_exec_time = (last_event_time - run_end_time).total_seconds()
            add_event = [last_event_title, event_exec_time]
            event_execution_times.append(add_event)
            sorted_events = sorted(event_execution_times, reverse=True, key=lambda field: field[1])
            if len(sorted_events) > 10:
                sorted_events = sorted_events[:10]
        else:
            events_list = False

        context = {
            'timezones': pytz.common_timezones,
            'certname': certname,
            'report_timestamp': report_timestamp,
            'hashid': hashid,
            'events_list': events_list,
            'event_durations': sorted_events,
            'environment': environment,
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
                                      )
        context = {
            'timezones': pytz.common_timezones,
            'certname': certname,
            'facts_list': facts_list,
        }

        return render(request, 'pano/facts.html', context)


@login_required
def filebucket(request):
    certname = request.GET.get('certname', False)
    rtype = request.GET.get('rtype', False)
    rtitle = request.GET.get('rtitle', False)
    md5_sum_from = request.GET.get('md5_from', False)
    env = request.GET.get('environment', False)
    file_status = request.GET.get('file_status', 'from')

    md5_sum_to = request.GET.get('md5_to', False)
    diff_files = request.GET.get('diff', False)
    if diff_files is not False:
        diff_files = True

    # If got md5_sum_from
    if certname and md5_sum_from and env and rtitle and rtype and file_status == 'from':
        filebucket_file = get_filebucket(certname=certname, environment=env, rtitle=rtitle, rtype=rtype,
                                         file_status=file_status,
                                         md5sum_from=md5_sum_from)
        if filebucket_file:
            context = {
                'timezones': pytz.common_timezones,
                'certname': certname,
                'content': filebucket_file,
                'isdiff': diff_files,
            }
            return render(request, 'pano/filebucket.html', context)
        else:
            return HttpResponse('Could not find file with MD5 Hash: %s in filebucket.' % (md5_sum_from))
    # If got md5_sum_to
    elif certname and md5_sum_to and env and rtitle and rtype and file_status == 'to':
        filebucket_file = get_filebucket(certname=certname, environment=env, rtitle=rtitle, rtype=rtype,
                                         file_status=file_status,
                                         md5sum_to=md5_sum_to)
        if filebucket_file:
            context = {
                'timezones': pytz.common_timezones,
                'certname': certname,
                'content': filebucket_file,
                'isdiff': diff_files,
            }
            return render(request, 'pano/filebucket.html', context)
        else:
            return HttpResponse('Could not find file with MD5 Hash: %s in filebucket.' % (md5_sum_from))
    elif certname and md5_sum_to and md5_sum_from and env and rtitle and rtype and file_status == 'both' and diff_files:
        filebucket_file = get_filebucket(certname=certname, environment=env, rtitle=rtitle, rtype=rtype,
                                         file_status=file_status,
                                         md5sum_to=md5_sum_to,
                                         md5sum_from=md5_sum_from,
                                         diff=diff_files)
        context = {
            'certname': certname,
            'content': filebucket_file,
            'isdiff': diff_files
        }

        return render(request, 'pano/filebucket.html', context)


    else:
        return HttpResponse('No valid GET params was sent.')


@login_required
@cache_page(CACHE_TIME)
def event_analytics(request, view='summary'):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    summary = events.get_events_summary(timespan='latest')

    context = {
        'timezones': pytz.common_timezones,
        'summary': summary,
    }
    # Show Classes
    if request.GET.get('value', False):
        if view == 'classes':
            class_name = request.GET.get('value')
            title = "Class: %s" % class_name
            class_events = events.get_report(key='containing-class', value=class_name)
            context['events'] = class_events
        # Show Nodes
        elif view == 'nodes':
            node_name = request.GET.get('value')
            title = "Node: %s" % node_name
            node_events = events.get_report(key='certname', value=node_name)
            context['events'] = node_events
        # Show Resources
        elif view == 'resources':
            resource_name = request.GET.get('value')
            title = "Resource: %s" % resource_name
            resource_events = events.get_report(key='resource-title', value=resource_name)
            context['events'] = resource_events
        # Show Types
        elif view == 'types':
            type_name = request.GET.get('value')
            title = "Type: %s" % type_name
            type_events = events.get_report(key='resource-type', value=type_name)
            context['events'] = type_events
    # Show summary if none of the above matched
    else:
        sum_avail = ['classes', 'nodes', 'resources', 'types']
        stat_avail = ['failed', 'noop', 'success', 'skipped'
                                                   '']
        show_summary = request.GET.get('show_summary', 'classes')
        show_status = request.GET.get('show_status', 'failed')
        if show_summary in sum_avail and show_status in stat_avail:
            title = "%s with status %s" % (show_summary.capitalize(), show_status.capitalize())
            context['show_title'] = title
        else:
            title = 'Failed Classes'
            context['show_title'] = title
        return render(request, 'pano/analytics/events_details.html', context)
    # Add title to context
    context['show_title'] = title
    # if the above went well and did not reach the else clause we can also return the awesome.
    return render(request, 'pano/analytics/events_inspect.html', context)


@login_required
def api(request):
    return False
