import queue
from threading import Thread

from django.shortcuts import redirect, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseBadRequest
import pytz

from pano.puppetdb import puppetdb
from pano.puppetdb import pdbutils
from pano.methods.dictfuncs import dictstatus as dictstatus


def splash(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['url'])
    else:
        context = {'timezones': pytz.common_timezones}
        return render(request, 'pano/splash.html', context)


def index(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['url'])
    else:
        num_threads = 6
        jobs_q = queue.Queue()
        out_q = queue.Queue()

        def db_threaded_requests(i, q):
            while True:
                t_job = q.get()
                t_path = t_job['path']
                t_params = t_job.get('params', {})
                t_verify = t_job.get('verify', False)
                t_api_v = t_job.get('api', 'v3')
                results = puppetdb.api_get(
                    path=t_path,
                    params=puppetdb.mk_puppetdb_query(t_params),
                    api_version=t_api_v,
                    verify=t_verify,
                )
                out_q.put({t_job['id']: results})
                q.task_done()

        for i in range(num_threads):
            worker = Thread(target=db_threaded_requests, args=(i, jobs_q))
            worker.setDaemon(True)
            worker.start()
        events_params = {
            'query':
                {
                    1: '["=","latest-report?",true]'
                },
            'summarize-by': 'certname',
        }
        # get 25 nodes that recently checked in
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

        for job in jobs:
            jobs_q.put(jobs[job])
        jobs_q.join()
        job_results = {}
        while True:
            try:
                msg = (out_q.get_nowait())
                job_results = dict(
                    list(job_results.items()) + list(msg.items()))
            except queue.Empty:
                break

        puppet_population = job_results['population']
        # Total resources managed by puppet metric
        total_resources = job_results['tot_resource']
        # Average resource per node metric
        avg_resource_node = job_results['avg_resource']
        # Information about all active nodes in puppet
        all_nodes_list = job_results['all_nodes']
        # All available events for the latest puppet reports
        event_list = job_results['event-counts']
        node_list = job_results['nodes']

        node_fail_count = 0
        node_unreported = 0
        node_change_count = 0

        for node in all_nodes_list:
            if pdbutils.is_unreported(node['report_timestamp']):
                node_unreported += 1
            for node_event in event_list:
                if node_event['subject']['title'] == node['name']:
                    if int(node_event['failures']) > 0:
                        node_fail_count += 1
                    elif int(node_event['failures']) == 0 \
                            and int(node_event['noops']) == 0 \
                            and int(node_event['skips']) == 0:
                        node_change_count += 1

        # for each node in the node_list, find out if the latest run has any failures
        # v3/event-counts --data-urlencode query='["=","latest-report?",true]'
        # --data-urlencode summarize-by='certname'

        """
        nodes_status:
            host1:
                failure: 0
                success: 100
                noop: 0
                skipped: 1
        """

        nodes_status = {}
        for node in node_list:
            for event_sum in event_list:
                if event_sum['subject']['title'] == node['name']:
                    nodes_status[node['name']] = {
                        'failure': event_sum['failures'],
                        'success': event_sum['successes'],
                        'noop': event_sum['noops'],
                        'skipped': event_sum['skips'],
                    }
        context = {'node_list': node_list,
                   'runstatus': nodes_status,
                   'certname': certname,
                   'timezones': pytz.common_timezones,
                   'population': puppet_population['Value'],
                   'total_resource': total_resources['Value'],
                   'avg_resource': "{:.2f}".format(avg_resource_node['Value']),
                   'failed_nodes': node_fail_count,
                   'changed_nodes': node_change_count,
                   'unreported_nodes': node_unreported,
                   }
        return render(request, 'pano/index.html', context)


def indexfailed(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['url'])
    else:
        num_threads = 6
        jobs_q = queue.Queue()
        out_q = queue.Queue()

        def db_threaded_requests(i, q):
            while True:
                t_job = q.get()
                t_path = t_job['path']
                t_params = t_job.get('params', {})
                t_verify = t_job.get('verify', False)
                t_api_v = t_job.get('api', 'v3')
                results = puppetdb.api_get(
                    path=t_path,
                    params=puppetdb.mk_puppetdb_query(t_params),
                    api_version=t_api_v,
                    verify=t_verify,
                )
                out_q.put({t_job['id']: results})
                q.task_done()

        for i in range(num_threads):
            worker = Thread(target=db_threaded_requests, args=(i, jobs_q))
            worker.setDaemon(True)
            worker.start()
        events_params = {
            'query':
                {
                    1: '["=","latest-report?",true]'
                },
            'summarize-by': 'certname',
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
                'verify': False,
            },
        }

        for job in jobs:
            jobs_q.put(jobs[job])
        jobs_q.join()
        job_results = {}
        while True:
            try:
                msg = (out_q.get_nowait())
                job_results = dict(
                    list(job_results.items()) + list(msg.items()))
            except queue.Empty:
                break

        puppet_population = job_results['population']
        # Total resources managed by puppet metric
        total_resources = job_results['tot_resource']
        # Average resource per node metric
        avg_resource_node = job_results['avg_resource']
        # Information about all active nodes in puppet
        all_nodes_list = job_results['all_nodes']
        # All available events for the latest puppet reports
        event_list = job_results['event-counts']
        node_list = job_results['nodes']

        merged_list = dictstatus(
            node_list, event_list, sort=True, get_status="failed")

        node_fail_count = 0
        node_unreported = 0
        node_change_count = 0
        for node in all_nodes_list:
            if pdbutils.is_unreported(node['report_timestamp']):
                node_unreported += 1
            for node_event in event_list:
                if node_event['subject']['title'] == node['name']:
                    if int(node_event['failures']) > 0:
                        node_fail_count += 1
                    elif int(node_event['failures']) == 0 \
                            and int(node_event['noops']) == 0 \
                            and int(node_event['skips']) == 0:
                        node_change_count += 1

        context = {'node_list': merged_list,
                   'certname': certname,
                   'unreported_nodes': node_unreported,
                   'timezones': pytz.common_timezones,
                   'population': puppet_population['Value'],
                   'total_resource': total_resources['Value'],
                   'avg_resource': "{:.2f}".format(avg_resource_node['Value']),
                   'failed_nodes': node_fail_count,
                   'changed_nodes': node_change_count,
                   }
        return render(request, 'pano/dashfailed.html', context)


def indexunreported(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['url'])
    else:
        num_threads = 6
        jobs_q = queue.Queue()
        out_q = queue.Queue()

        def db_threaded_requests(i, q):
            while True:
                t_job = q.get()
                t_path = t_job['path']
                t_params = t_job.get('params', {})
                t_verify = t_job.get('verify', False)
                t_api_v = t_job.get('api', 'v3')
                results = puppetdb.api_get(
                    path=t_path,
                    params=puppetdb.mk_puppetdb_query(t_params),
                    api_version=t_api_v,
                    verify=t_verify,
                )
                out_q.put({t_job['id']: results})
                q.task_done()

        for i in range(num_threads):
            worker = Thread(target=db_threaded_requests, args=(i, jobs_q))
            worker.setDaemon(True)
            worker.start()
        events_params = {
            'query':
                {
                    1: '["=","latest-report?",true]'
                },
            'summarize-by': 'certname',
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
                'verify': False,
            },
        }

        for job in jobs:
            jobs_q.put(jobs[job])
        jobs_q.join()
        job_results = {}
        while True:
            try:
                msg = (out_q.get_nowait())
                job_results = dict(
                    list(job_results.items()) + list(msg.items()))
            except queue.Empty:
                break

        puppet_population = job_results['population']
        # Total resources managed by puppet metric
        total_resources = job_results['tot_resource']
        # Average resource per node metric
        avg_resource_node = job_results['avg_resource']
        # Information about all active nodes in puppet
        all_nodes_list = job_results['all_nodes']
        # All available events for the latest puppet reports
        event_list = job_results['event-counts']
        node_list = job_results['nodes']

        merged_list = dictstatus(
            node_list, event_list, sort=True, get_status="unreported")

        node_fail_count = 0
        node_unreported = 0
        node_change_count = 0
        for node in all_nodes_list:
            if pdbutils.is_unreported(node['report_timestamp']):
                node_unreported += 1
            for node_event in event_list:
                if node_event['subject']['title'] == node['name']:
                    if int(node_event['failures']) > 0:
                        node_fail_count += 1
                    elif int(node_event['failures']) == 0 \
                            and int(node_event['noops']) == 0 \
                            and int(node_event['skips']) == 0:
                        node_change_count += 1

        context = {'node_list': merged_list,
                   'certname': certname,
                   'unreported_nodes': node_unreported,
                   'timezones': pytz.common_timezones,
                   'population': puppet_population['Value'],
                   'total_resource': total_resources['Value'],
                   'avg_resource': "{:.2f}".format(avg_resource_node['Value']),
                   'failed_nodes': node_fail_count,
                   'changed_nodes': node_change_count,
                   }
        return render(request, 'pano/dashunreported.html', context)


def indexchanged(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['url'])
    else:
        num_threads = 6
        jobs_q = queue.Queue()
        out_q = queue.Queue()

        def db_threaded_requests(i, q):
            while True:
                t_job = q.get()
                t_path = t_job['path']
                t_params = t_job.get('params', {})
                t_verify = t_job.get('verify', False)
                t_api_v = t_job.get('api', 'v3')
                results = puppetdb.api_get(
                    path=t_path,
                    params=puppetdb.mk_puppetdb_query(t_params),
                    api_version=t_api_v,
                    verify=t_verify,
                )
                out_q.put({t_job['id']: results})
                q.task_done()

        for i in range(num_threads):
            worker = Thread(target=db_threaded_requests, args=(i, jobs_q))
            worker.setDaemon(True)
            worker.start()
        events_params = {
            'query':
                {
                    1: '["=","latest-report?",true]'
                },
            'summarize-by': 'certname',
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
                'verify': False,
            },
        }

        for job in jobs:
            jobs_q.put(jobs[job])
        jobs_q.join()
        job_results = {}
        while True:
            try:
                msg = (out_q.get_nowait())
                job_results = dict(
                    list(job_results.items()) + list(msg.items()))
            except queue.Empty:
                break

        puppet_population = job_results['population']
        # Total resources managed by puppet metric
        total_resources = job_results['tot_resource']
        # Average resource per node metric
        avg_resource_node = job_results['avg_resource']
        # Information about all active nodes in puppet
        all_nodes_list = job_results['all_nodes']
        # All available events for the latest puppet reports
        event_list = job_results['event-counts']
        node_list = job_results['nodes']

        merged_list = dictstatus(
            node_list, event_list, get_status="changed")

        node_fail_count = 0
        node_unreported = 0
        node_change_count = 0
        for node in all_nodes_list:
            if pdbutils.is_unreported(node['report_timestamp']):
                node_unreported += 1
            for node_event in event_list:
                if node_event['subject']['title'] == node['name']:
                    if int(node_event['failures']) > 0:
                        node_fail_count += 1
                    elif int(node_event['failures']) == 0 \
                            and int(node_event['noops']) == 0 \
                            and int(node_event['skips']) == 0:
                        node_change_count += 1

        context = {'node_list': merged_list,
                   'certname': certname,
                   'unreported_nodes': node_unreported,
                   'timezones': pytz.common_timezones,
                   'population': puppet_population['Value'],
                   'total_resource': total_resources['Value'],
                   'avg_resource': "{:.2f}".format(avg_resource_node['Value']),
                   'failed_nodes': node_fail_count,
                   'changed_nodes': node_change_count,
                   }
        return render(request, 'pano/dashchanged.html', context)


def nodes(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
        try:
            limits = int(request.GET.get('limits', 50))
            if limits is 0:
                limits = 50
        except:
            return HttpResponseBadRequest('Oh no! Your filters were invalid.')
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
            }
        else:
            node_params = {
                'query': {},
            }

        node_list = puppetdb.api_get(path='/nodes',
                                     params=puppetdb.mk_puppetdb_query(
                                         node_params),
                                     verify=False)

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

        paginator = Paginator(merged_list, limits)  # Show 25 contacts per page
        page = request.GET.get('page')
        try:
            merged_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            merged_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of
            # results.
            merged_list = paginator.page(paginator.num_pages)
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
        }
        return render(request, 'pano/nodes.html', context)


def reports(request, certname=None):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
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
        }
        reports_list = puppetdb.api_get(path='/reports',
                                        api_version='v4',
                                        params=puppetdb.mk_puppetdb_query(
                                            reports_params),
                                        verify=False)

        report_status = {}
        # this will take a long time if there are lots of reports...
        # TODO : please use celery workers or it will take light years to
        # finish...
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

        paginator = Paginator(reports_list, 25)  # Show 25 contacts per page
        page = request.GET.get('page')
        try:
            reports_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            reports_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of
            # results.
            reports_list = paginator.page(paginator.num_pages)
        context = {
            'timezones': pytz.common_timezones,
            'certname': certname,
            'reports': reports_list,
            'report_status': report_status,
        }

        return render(request, 'pano/reports.html', context)


def events(request, certname=None, hashid=None):
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

        return render(request, 'pano/events.html', context)


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
