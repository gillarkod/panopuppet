import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, redirect
from django.views.decorators.cache import cache_page

from panopuppet.pano.methods.dictfuncs import dictstatus as dictstatus
from panopuppet.pano.puppetdb.pdbutils import run_puppetdb_jobs
from panopuppet.pano.puppetdb.puppetdb import set_server, get_server
from panopuppet.pano.settings import CACHE_TIME

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

    jobs = {
        'tot_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'tot_resource',
            'path': 'mbeans/puppetlabs.puppetdb.query.population:type=default,name=num-resources',
        },
        'avg_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'avg_resource',
            'path': 'mbeans/puppetlabs.puppetdb.query.population:type=default,name=avg-resources-per-node',
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

    failed_list, changed_list, unreported_list, mismatch_list, pending_list = dictstatus(all_nodes_list,
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

    return HttpResponse(json.dumps(context), content_type="application/json")


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

    failed_list, changed_list, unreported_list, mismatch_list, pending_list = dictstatus(all_nodes_list,
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

    return HttpResponse(json.dumps(context), content_type="application/json")


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

    jobs = {
        'tot_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'tot_resource',
            'path': 'mbeans/puppetlabs.puppetdb.query.population:type=default,name=num-resources',
        },
        'avg_resource': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'id': 'avg_resource',
            'path': 'mbeans/puppetlabs.puppetdb.query.population:type=default,name=avg-resources-per-node',
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

    failed_list, changed_list, unreported_list, mismatch_list, pending_list = dictstatus(all_nodes_list,
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
    context['population'] = puppet_population
    context['total_resource'] = total_resources['Value']
    context['avg_resource'] = "{:.2f}".format(avg_resource_node['Value'])
    context['failed_nodes'] = node_fail_count
    context['changed_nodes'] = node_change_count
    context['unreported_nodes'] = node_unreported_count
    context['mismatching_timestamps'] = node_off_timestamps_count
    context['pending_nodes'] = node_pending_count

    return HttpResponse(json.dumps(context), content_type="application/json")
