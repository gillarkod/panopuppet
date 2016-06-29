import json
from datetime import timedelta

import arrow
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, redirect
from django.views.decorators.cache import cache_page

from panopuppet.pano.methods.dictfuncs import dictstatus as dictstatus
from panopuppet.pano.puppetdb.pdbutils import run_puppetdb_jobs
from panopuppet.pano.puppetdb.puppetdb import set_server, get_server
from panopuppet.pano.settings import CACHE_TIME

from requests.structures import CaseInsensitiveDict
from django.template import defaultfilters as filters
from django.utils.timezone import localtime
from panopuppet.pano.puppetdb.pdbutils import json_to_datetime, is_unreported
import arrow

__author__ = 'etaklar'


@cache_page(CACHE_TIME)
def dashboard_status_json(request):
    context = {}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    source_url, source_certs, source_verify = get_server(request)
    pdb_vers = get_server(request, type='puppetdb_vers')

    puppet_run_time = get_server(request, type='run_time')

    events_params = {
        'query':
            {
                1: '["and",["=","latest_report?",true],["in", "certname",["extract", "certname",["select_nodes",["null?","deactivated",true]]]]]'
            },
        'summarize_by': 'certname',
    }
    reports_params = {
        'query':
            {
                1: '["and",["=","latest_report?",true],["in", "certname",["extract", "certname",["select_nodes",["null?","deactivated",true]]]]]'
            }
    }

    if pdb_vers == 4:
        tot_res_path = 'mbeans/puppetlabs.puppetdb.population:name=num-resources'
        avg_res_path = 'mbeans/puppetlabs.puppetdb.population:name=avg-resources-per-node'
    else:
        tot_res_path = 'mbeans/puppetlabs.puppetdb.query.population:type=default,name=num-resources'
        avg_res_path = 'mbeans/puppetlabs.puppetdb.query.population:type=default,name=avg-resources-per-node'

    jobs = {
        'tot_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'tot_resource',
            'path': tot_res_path,
        },
        'avg_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'avg_resource',
            'path': avg_res_path,
        },
        'all_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'all_nodes',
            'path': '/nodes',
            'request': request
        },
        'reports': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'reports',
            'path': '/reports',
            'params': reports_params,
            'request': request
        },
        'events': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'event_counts',
            'path': 'event-counts',
            'api_version': 'v4',
            'params': events_params,
            'request': request
        },
    }
    puppetdb_results = run_puppetdb_jobs(jobs)

    # Assign vars from the completed jobs
    # Number of results from all_nodes is our population.
    puppet_population = len(puppetdb_results['all_nodes'])

    # Total resources managed by puppet metric
    total_resources = puppetdb_results['tot_resource'].get('value', puppetdb_results['tot_resource'])

    # Average resource per node metric
    avg_resource_node = puppetdb_results['avg_resource'].get('value', puppetdb_results['avg_resource'])

    # Information about all active nodes in puppet
    all_nodes_list = puppetdb_results['all_nodes']

    # All available events for the latest puppet reports
    event_list = puppetdb_results['event_counts']
    event_dict = {item['subject']['title']: item for item in event_list}
    # All of the latest reports
    reports_list = puppetdb_results['reports']
    reports_dict = {item['certname']: item for item in reports_list}

    failed_list, changed_list, unreported_list, mismatch_list, pending_list = dictstatus(
        all_nodes_list,
        reports_dict,
        event_dict,
        sort=True,
        sortby='latestReport',
        get_status='notall',
        puppet_run_time=puppet_run_time)

    pending_list = [x for x in pending_list if x not in unreported_list]
    changed_list = [x for x in changed_list if
                    x not in unreported_list and x not in failed_list and x not in pending_list]
    failed_list = [x for x in failed_list if x not in unreported_list]
    unreported_list = [x for x in unreported_list if x not in failed_list]

    node_unreported_count = len(unreported_list)
    node_fail_count = len(failed_list)
    node_change_count = len(changed_list)
    node_off_timestamps_count = len(mismatch_list)
    node_pending_count = len(pending_list)

    context['population'] = puppet_population
    context['total_resource'] = total_resources['Value']
    context['avg_resource'] = "{:.2f}".format(avg_resource_node['Value'])
    context['failed_nodes'] = node_fail_count
    context['changed_nodes'] = node_change_count
    context['unreported_nodes'] = node_unreported_count
    context['mismatching_timestamps'] = node_off_timestamps_count
    context['pending_nodes'] = node_pending_count

    return HttpResponse(json.dumps(context, indent=2), content_type="application/json")


@login_required
@cache_page(CACHE_TIME)
def dashboard_nodes_json(request):
    context = {}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    source_url, source_certs, source_verify = get_server(request)

    puppet_run_time = get_server(request, type='run_time')

    # Dashboard to show nodes of "recent, failed, unreported or changed"
    dashboard_show = request.GET.get('show', 'recent')
    events_params = {
        'query':
            {
                1: '["and",["=","latest_report?",true],["in", "certname",["extract", "certname",["select_nodes",["null?","deactivated",true]]]]]'
            },
        'summarize_by': 'certname',
    }
    all_nodes_params = {
        'query':
            {
                1: '["and",["=","latest_report?",true],["in", "certname",["extract", "certname",["select_nodes",["null?","deactivated",true]]]]]'
            },
    }
    reports_params = {
        'query':
            {
                1: '["and",["=","latest_report?",true],["in", "certname",["extract", "certname",["select_nodes",["null?","deactivated",true]]]]]'
            }
    }
    nodes_params = {
        'limit': 25,
        'order_by': {
            'order_field': {
                'field': 'report_timestamp',
                'order': 'desc',
            },
            'query_field': {'field': 'certname'},
        },
    }

    jobs = {
        'all_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'all_nodes',
            'path': '/nodes',
            'request': request
        },
        'events': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'event_counts',
            'path': 'event-counts',
            'api_version': 'v4',
            'params': events_params,
            'request': request
        },
        'nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'nodes',
            'path': '/nodes',
            'params': nodes_params,
            'request': request
        },
        'reports': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'reports',
            'path': '/reports',
            'params': reports_params,
            'request': request
        },
    }

    puppetdb_results = run_puppetdb_jobs(jobs)
    # Information about all active nodes in puppet
    all_nodes_list = puppetdb_results['all_nodes']
    # All available events for the latest puppet reports
    event_list = puppetdb_results['event_counts']
    event_dict = {item['subject']['title']: item for item in event_list}
    # All of the latest reports
    reports_list = puppetdb_results['reports']
    reports_dict = {item['certname']: item for item in reports_list}
    # 25 Nodes
    node_list = puppetdb_results['nodes']

    failed_list, changed_list, unreported_list, mismatch_list, pending_list = dictstatus(
        all_nodes_list,
        reports_dict,
        event_dict,
        sort=True,
        sortby='latestReport',
        get_status='notall',
        puppet_run_time=puppet_run_time)

    pending_list = [x for x in pending_list if x not in unreported_list]
    changed_list = [x for x in changed_list if
                    x not in unreported_list and x not in failed_list and x not in pending_list]
    failed_list = [x for x in failed_list if x not in unreported_list]
    unreported_list = [x for x in unreported_list if x not in failed_list]

    if dashboard_show == 'recent':
        merged_nodes_list = dictstatus(
            node_list, reports_dict, event_dict, sort=False, get_status="all", puppet_run_time=puppet_run_time)
    elif dashboard_show == 'failed':
        merged_nodes_list = failed_list
    elif dashboard_show == 'unreported':
        merged_nodes_list = unreported_list
    elif dashboard_show == 'changed':
        merged_nodes_list = changed_list
    elif dashboard_show == 'mismatch':
        merged_nodes_list = mismatch_list
    elif dashboard_show == 'pending':
        merged_nodes_list = pending_list
    else:
        merged_nodes_list = dictstatus(
            node_list, reports_dict, event_dict, sort=False, get_status="all", puppet_run_time=puppet_run_time)

    context['node_list'] = merged_nodes_list
    context['selected_view'] = dashboard_show

    return HttpResponse(json.dumps(context, indent=2), content_type="application/json")


@login_required
@cache_page(CACHE_TIME)
def dashboard_json(request):
    context = {}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    source_url, source_certs, source_verify = get_server(request)
    pdb_vers = get_server(request, type='puppetdb_vers')
    puppet_run_time = get_server(request, type='run_time')
    dashboard_show = request.GET.get('show', 'recent')
    events_params = {
        'query':
            {
                1: '["and",["=","latest_report?",true],["in", "certname",["extract", "certname",["select_nodes",["null?","deactivated",true]]]]]'
            },
        'summarize_by': 'certname',
    }
    reports_params = {
        'query':
            {
                1: '["and",["=","latest_report?",true],["in", "certname",["extract", "certname",["select_nodes",["null?","deactivated",true]]]]]'
            }
    }
    nodes_params = {
        'limit': 25,
        'order_by': {
            'order_field': {
                'field': 'report_timestamp',
                'order': 'desc',
            },
            'query_field': {'field': 'certname'},
        },
    }

    if pdb_vers == 4:
        tot_res_path = 'mbeans/puppetlabs.puppetdb.population:name=num-resources'
        avg_res_path = 'mbeans/puppetlabs.puppetdb.population:name=avg-resources-per-node'
    else:
        tot_res_path = 'mbeans/puppetlabs.puppetdb.query.population:type=default,name=num-resources'
        avg_res_path = 'mbeans/puppetlabs.puppetdb.query.population:type=default,name=avg-resources-per-node'

    jobs = {
        'tot_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'tot_resource',
            'path': tot_res_path,
        },
        'avg_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'avg_resource',
            'path': avg_res_path,
        },
        'all_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'all_nodes',
            'path': '/nodes',
            'request': request
        },
        'events': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'event_counts',
            'path': '/event-counts',
            'api_version': 'v4',
            'params': events_params,
            'request': request
        },
        'reports': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'reports',
            'path': '/reports',
            'params': reports_params,
            'request': request
        },
        'nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'nodes',
            'path': '/nodes',
            'params': nodes_params,
            'request': request
        },
    }
    puppetdb_results = run_puppetdb_jobs(jobs)

    # Assign vars from the completed jobs
    # Number of results from all_nodes is our population.
    puppet_population = len(puppetdb_results['all_nodes'])
    # Total resources managed by puppet metric
    total_resources = puppetdb_results['tot_resource']

    # Average resource per node metric
    avg_resource_node = puppetdb_results['avg_resource']

    # Information about all active nodes in puppet
    all_nodes_list = puppetdb_results['all_nodes']
    # All available events for the latest puppet reports
    event_list = puppetdb_results['event_counts']
    event_dict = {item['subject']['title']: item for item in event_list}
    # All of the latest reports
    reports_list = puppetdb_results['reports']
    reports_dict = {item['certname']: item for item in reports_list}
    # 25 Nodes
    node_list = puppetdb_results['nodes']

    failed_list, changed_list, unreported_list, mismatch_list, pending_list = dictstatus(
        all_nodes_list,
        reports_dict,
        event_dict,
        sort=True,
        sortby='latestReport',
        get_status='notall',
        puppet_run_time=puppet_run_time)

    pending_list = [x for x in pending_list if x not in unreported_list]
    changed_list = [x for x in changed_list if
                    x not in unreported_list and x not in failed_list and x not in pending_list]
    failed_list = [x for x in failed_list if x not in unreported_list]
    unreported_list = [x for x in unreported_list if x not in failed_list]

    node_unreported_count = len(unreported_list)
    node_fail_count = len(failed_list)
    node_change_count = len(changed_list)
    node_off_timestamps_count = len(mismatch_list)
    node_pending_count = len(pending_list)

    if dashboard_show == 'recent':
        merged_nodes_list = dictstatus(node_list,
                                       reports_dict,
                                       event_dict,
                                       sort=False,
                                       get_status="all",
                                       puppet_run_time=puppet_run_time)
    elif dashboard_show == 'failed':
        merged_nodes_list = failed_list
    elif dashboard_show == 'unreported':
        merged_nodes_list = unreported_list
    elif dashboard_show == 'changed':
        merged_nodes_list = changed_list
    elif dashboard_show == 'mismatch':
        merged_nodes_list = mismatch_list
    elif dashboard_show == 'pending':
        merged_nodes_list = pending_list
    else:
        merged_nodes_list = dictstatus(node_list,
                                       reports_dict,
                                       event_dict,
                                       sort=False,
                                       get_status="all",
                                       puppet_run_time=puppet_run_time)

    context['node_list'] = merged_nodes_list
    context['selected_view'] = dashboard_show
    context['population'] = puppet_population
    context['total_resource'] = total_resources['Value']
    context['avg_resource'] = "{:.2f}".format(avg_resource_node['Value'])
    context['failed_nodes'] = node_fail_count
    context['changed_nodes'] = node_change_count
    context['unreported_nodes'] = node_unreported_count
    context['mismatching_timestamps'] = node_off_timestamps_count
    context['pending_nodes'] = node_pending_count

    return HttpResponse(json.dumps(context, indent=2), content_type="application/json")


@cache_page(CACHE_TIME)
def dashboard_test_json(request):
    context = {}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    source_url, source_certs, source_verify = get_server(request)
    pdb_vers = get_server(request, type='puppetdb_vers')
    puppet_run_time = get_server(request, type='run_time')

    dashboard_show = request.GET.get('show', 'recent')

    # Datatables data fetch
    dashboard_dt_search = request.GET.get('search[value]', '.*')
    dashboard_dt_limit = request.GET.get('length', 25)
    dashboard_dt_offset = request.GET.get('start', 0)
    # Order by Column
    dashboard_dt_colOr = request.GET.get('order[0][column]', '2')
    # Order direction (desc, asc)
    dashboard_dt_dirOr = request.GET.get('order[0][column]', '2')

    dashboard_order_table = {
        0: 'certname',
        1: 'catalog_timestamp',
        2: 'report_timestamp',
        3: 'facts_timestamp',
        4: 'succcesses',
        5: 'noops',
        6: 'failures',
        7: 'skips',
    }

    datatable_req = False

    if pdb_vers == 4:
        tot_res_path = 'mbeans/pu§etlabs.puppetdb.population:name=num-resources'
        avg_res_path = 'mbeans/puppetlabs.puppetdb.population:name=avg-resources-per-node'
    else:
        tot_res_path = 'mbeans/puppetlabs.puppetdb.query.population:type=default,name=num-resources'
        avg_res_path = 'mbeans/puppetlabs.puppetdb.query.population:type=default,name=avg-resources-per-node'

    # Stuff that should be returned from the GET parameters
    if request.GET.get('draw', False):
        context['draw'] = int(request.GET.get('draw'))
        datatable_req = True

    def merge_two_params(x, y):
        """
        Given two dicts, merge them into a new dict as a shallow copy.
        If its a dashboard status request it will not merge and return x.
        """
        if not datatable_req:
            z = x.copy()
            z.update(y)
            return z
        else:
            return x

    def merge_two_dicts(x, y):
        """Given two dicts, merge them into a new dict as a shallow copy."""
        z = x.copy()
        z.update(y)
        return z

    puppet_last_run_time = arrow.utcnow()
    puppet_last_run_time = puppet_last_run_time.replace(minutes=-puppet_run_time)

    if dashboard_show == 'unreported':
        puppet_timestamp_logic = '<'
    else:
        puppet_timestamp_logic = '>='

    if dashboard_show == 'recent':
        subquery_status = ''
    elif dashboard_show in ['failed', 'changed']:
        subquery_status = ',["=","latest_report_status","%s"]' % dashboard_show
    elif dashboard_show == 'pending':
        subquery_status = ',["%s","report_timestamp","%s"],' \
                          '["in", "certname", ' \
                          '["extract", "certname", ' \
                          '["select_reports", ' \
                          '["and",["=", "noop", true],' \
                          '["=","latest_report?", true] ' \
                          ']]]]'

    events_params = {
        'query':
            {
                1: '["and",'
                   '["=","latest_report?",true],'
                   '["in", "certname",'
                   '["extract", "certname",'
                   '["select_nodes",'
                   '["and",'
                   '["null?","deactivated",true],'
                   '["%s","report_timestamp","%s"]'
                   '%s'
                   ']]]]]' % (puppet_timestamp_logic, puppet_last_run_time, subquery_status)
            },
        'summarize_by': 'certname',
    }
    node_count_params = {
        'limit': 1,
        'include_total': 'true'
    }
    failed_nodes_params = {
        'query':
            {
                'operator': 'and',
                1: '["=","latest_report_status","failed"]',
                2: '["%s","report_timestamp","%s"]' % (puppet_timestamp_logic, puppet_last_run_time)
            }
    }
    changed_nodes_params = {
        'query':
            {
                'operator': 'and',
                1: '["=","latest_report_status","changed"]',
                2: '["%s","report_timestamp","%s"]' % (puppet_timestamp_logic, puppet_last_run_time)
            }
    }
    noop_nodes_params = {
        'query':
            {
                1: '["and",'
                   '["%s","report_timestamp","%s"],'
                   '["in", "certname", '
                   '["extract", "certname", '
                   '["select_reports", '
                   '["and",["=", "noop", true],'
                   '["=","latest_report?", true] '
                   ']]]]]' % (puppet_timestamp_logic, puppet_last_run_time)
            }
    }
    unreported_nodes_params = {
        'query':
            {
                1: '["<","report_timestamp","%s"]' % puppet_last_run_time
            }
    }

    default_jobs = {
        'tot_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'tot_resource',
            'path': tot_res_path,
        },
        'avg_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'avg_resource',
            'path': avg_res_path,
        },
        'events': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'event_counts',
            'path': '/event-counts',
            'api_version': 'v4',
            'params': events_params,
            'request': request
        },
        'recent_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'recent_nodes',
            'path': '/nodes',
            'request': request
        },
        'tot_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'tot_nodes',
            'path': '/nodes',
            'params': node_count_params,
            'request': request
        },
        'mismatch_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'mismatch_nodes',
            'path': '/nodes',
            'request': request
        },
        'unreported_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'vlimit4',
            'id': 'unreported_nodes',
            'path': '/nodes',
            'params': merge_two_params(unreported_nodes_params, node_count_params),
            'request': request
        },
        'failed_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'failed_nodes',
            'path': '/nodes',
            'params': merge_two_params(failed_nodes_params, node_count_params),
            'request': request
        },
        'changed_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'changed_nodes',
            'path': '/nodes',
            'params': merge_two_params(changed_nodes_params, node_count_params),
            'request': request
        },
        'pending_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',        # Only if search is used.
            'id': 'pending_nodes',
            'path': '/nodes',
            'params': merge_two_params(noop_nodes_params, node_count_params),
            'request': request
        },
    }

    if datatable_req:
        jobs = dict()
        jobs['events'] = default_jobs['events']
        jobs[dashboard_show + '_nodes'] = default_jobs[dashboard_show + '_nodes'].copy()
        # Add params for paging
        if dashboard_dt_limit:
            if 'params' in jobs[dashboard_show + '_nodes']:
                jobs[dashboard_show + '_nodes']['params']['limit'] = dashboard_dt_limit
                jobs[dashboard_show + '_nodes']['params']['offset'] = dashboard_dt_offset
                jobs[dashboard_show + '_nodes']['params']['include_total'] = 'true'
            else:
                jobs[dashboard_show + '_nodes']['params'] = {
                    'limit': dashboard_dt_limit,
                    'offset': dashboard_dt_offset,
                    'include_total': 'true'
                }

        # Add another call for limit 1 and include total so we can get the "true" amount of nodes for this status type
        # Only if search is used.
        if dashboard_dt_search:
            jobs[dashboard_show + '_nodes_count'] = default_jobs[dashboard_show + '_nodes'].copy()
            jobs[dashboard_show + '_nodes_count']['id'] = '%s_node_count' % dashboard_show
            if 'params' in jobs[dashboard_show + '_nodes_count']:
                jobs[dashboard_show + '_nodes_count']['params']['limit'] = '1'
                jobs[dashboard_show + '_nodes_count']['params']['include_total'] = 'true'
            else:
                jobs[dashboard_show + '_nodes_count']['params'] = {
                    'limit': '1',
                    'include_total': 'true'
                }
    elif not datatable_req:
        jobs = default_jobs
        jobs.pop('mismatch_nodes')
        jobs.pop('events')
        jobs.pop('recent_nodes')

    def check_mismatch_ts(node_data, puppet_run_interval=puppet_run_time):
        report_timestamp = node_data.get('report_timestamp', None)
        catalog_timestamp = node_data.get('catalog_timestamp', None)
        fact_timestamp = node_data.get('facts_timestamp', None)

        if report_timestamp is None or catalog_timestamp is None or fact_timestamp is None:
            return True

        # check if the fact report is older than puppet_run_time by double the run time
        report_time = arrow.get(report_timestamp)
        fact_time = arrow.get(fact_timestamp)
        catalog_time = arrow.get(catalog_timestamp)

        # Report time, fact time and catalog time should all be run within (PUPPET_RUN_INTERVAL / 2)
        # minutes of each other
        diffs = dict()
        # Time elapsed between fact time and catalog time
        diffs['catalog_fact'] = catalog_time - fact_time
        diffs['fact_catalog'] = fact_time - catalog_time

        # Time elapsed between fact time and report time
        diffs['report_fact'] = report_time - fact_time
        diffs['fact_report'] = fact_time - report_time
        # Time elapsed between report and catalog
        diffs['report_catalog'] = report_time - catalog_time
        diffs['catalog_report'] = catalog_time - report_time

        for key, value in diffs.items():
            if value > timedelta(minutes=puppet_run_interval / 2):
                return True
        return False

    puppetdb_results = run_puppetdb_jobs(jobs)

    # If dashboard status request (node counts only)
    if not datatable_req:
        context['failed_nodes'] = puppetdb_results['failed_nodes'][-1]['X-Records']
        context['changed_nodes'] = puppetdb_results['changed_nodes'][-1]['X-Records']
        context['noop_nodes'] = puppetdb_results['noop_nodes'][-1]['X-Records']
        context['unreported_nodes'] = puppetdb_results['unreported_nodes'][-1]['X-Records']
        context['puppet_population'] = puppetdb_results['tot_nodes'][-1]['X-Records']
        context['total_resources'] = puppetdb_results['tot_resource']
        context['avg_resource_node'] = puppetdb_results['avg_resource']

    elif datatable_req:
        if dashboard_dt_search:
            for res in puppetdb_results[dashboard_show + '_node_count']:
                if isinstance(res, CaseInsensitiveDict) and 'X-Records' in res:
                    context['recordsTotal'] = res['X-Records']
        else:
            context['recordsTotal'] = puppetdb_results[dashboard_show + '_nodes'][-1]['X-Records']

        # fetch nodes from the query
        nodes_list = puppetdb_results[dashboard_show + '_nodes'][0]
        resp_headers = puppetdb_results[dashboard_show + '_nodes'][-1]
        context['recordsFiltered'] = resp_headers['X-Records']
        # All available events for the latest puppet reports
        event_dict = {item['subject']['title']: item for item in puppetdb_results['event_counts']}

        nodes_dict = {item['certname']: item for item in nodes_list}

        _default_merge = {
            'failures': 0,
            'skips': 0,
            'successes': 0,
            'noops': 0
        }

        nodes_list = [
            merge_two_dicts(item, event_dict.get(item['certname'], _default_merge))
            for item in nodes_dict.values()
            if item['certname'] in event_dict
            ]

        # Convert timestamps to timezone set for user/site-wide
        for item in nodes_list:
            item['catalog_timestamp'] = filters.date(
                localtime(json_to_datetime(item['catalog_timestamp'])),
                'Y-m-d H:i:s') if item['catalog_timestamp'] is not None else ''

            item['report_timestamp'] = filters.date(
                localtime(json_to_datetime(item['report_timestamp'])),
                'Y-m-d H:i:s') if item['report_timestamp'] is not None else ''

            item['facts_timestamp'] = filters.date(
                localtime(json_to_datetime(item['facts_timestamp'])),
                'Y-m-d H:i:s') if item['facts_timestamp'] is not None else ''

        context['data'] = nodes_list

        # TODO: Add support for mismatching again after we identify a good way to solve slowness
        # _mismatching_nodes_dict = {
        #     item['certname']: item for item in recent_nodes_list if check_mismatch_ts(item) and
        #     item['certname'] not in _unreported_nodes_dict

    context['selected_view'] = dashboard_show
    # context['get_params'] = {key: value for key, value in request.GET.items() if 'column' not in key}

    # context['mismatching_timestamps'] = node_off_timestamps_count

    return HttpResponse(json.dumps(context, indent=2, sort_keys=True), content_type="application/json; charset=utf-8")
