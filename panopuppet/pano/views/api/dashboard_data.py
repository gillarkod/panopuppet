import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, redirect
from django.views.decorators.cache import cache_page

from panopuppet.pano.methods.dictfuncs import dictstatus as dictstatus
from panopuppet.pano.puppetdb.pdbutils import run_puppetdb_jobs
from panopuppet.pano.puppetdb.puppetdb import set_server, get_server
from panopuppet.pano.settings import CACHE_TIME
import arrow
from datetime import timedelta

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
    import datetime as dt
    a = dt.datetime.utcnow()
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
    failed_nodes_params = {
        'query':
            {
                1: '["=","latest_report_status","failed"]'
            }
    }
    changed_nodes_params = {
        'query':
            {
                1: '["=","latest_report_status","changed"]'
            }
    }
    noop_nodes_params = {
        'query':
            {
                1: '["in", "certname", ["extract", "certname", ["select_reports", ["and",["=", "noop", true],["=","latest_report?", true]]]]]'
            }
    }

    puppet_last_run_time = arrow.utcnow()
    puppet_last_run_time = puppet_last_run_time.replace(minutes=-puppet_run_time)
    unreported_nodes_params = {
        'query':
            {
                1: '["<","report_timestamp","%s"]' % puppet_last_run_time
            }
    }

    def merge_two_dicts(x, y):
        '''Given two dicts, merge them into a new dict as a shallow copy.'''
        z = x.copy()
        z.update(y)
        return z

    def check_mismatch_ts(
            node_data,
            puppet_run_interval=puppet_run_time
    ):
        """
        :param report_timestamp: str
        :param fact_timestamp: str
        :param catalog_timestamp: str
        :return: Bool
        Returns False if the compiled run has not failed
        Returns True if the compiled run has failed
        """
        import pprint

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
        'all_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'all_nodes',
            'path': '/nodes',
            'request': request
        },
        'unreported_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'unreported_nodes',
            'path': '/nodes',
            'params': unreported_nodes_params,
            'request': request
        },
        'failed_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'failed_nodes',
            'path': '/nodes',
            'params': failed_nodes_params,
            'request': request
        },
        'changed_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'changed_nodes',
            'path': '/nodes',
            'params': changed_nodes_params,
            'request': request
        },
        'noop_nodes': {
            'url': source_url,
            'certs': source_certs,
            'verify': source_verify,
            'api_version': 'v4',
            'id': 'noop_nodes',
            'path': '/nodes',
            'params': noop_nodes_params,
            'request': request
        },
    }

    puppetdb_results = run_puppetdb_jobs(jobs)
    b = dt.datetime.utcnow()
    print("API Calls Total: %s " % (b - a).total_seconds())
    # Assign vars from the completed jobs
    # Number of results from all_nodes is our population.
    puppet_population = len(puppetdb_results['all_nodes'])
    # Total resources managed by puppet metric
    total_resources = puppetdb_results['tot_resource']

    # Average resource per node metric
    avg_resource_node = puppetdb_results['avg_resource']

    # Information about all active nodes in puppet
    all_nodes_list = puppetdb_results['all_nodes']
    all_nodes_dict = {item['certname']: item for item in all_nodes_list}

    # All available events for the latest puppet reports
    event_list = puppetdb_results['event_counts']
    event_dict = {item['subject']['title']: item for item in event_list}

    # Information about all unreported nodes in puppet
    unreported_nodes_list = puppetdb_results['unreported_nodes']
    _unreported_nodes_dict = {
        item['certname']: item for item in unreported_nodes_list
        }

    _mismatching_nodes_dict = {
        item['certname']: item for item in all_nodes_list if check_mismatch_ts(item) and
        item['certname'] not in _unreported_nodes_dict
        }

    # Information about all failed nodes in puppet
    failed_nodes_list = puppetdb_results['failed_nodes']
    _failed_nodes_dict = {
        item['certname']: item for item in failed_nodes_list if
        item['certname'] not in _unreported_nodes_dict and
        item['certname'] not in _mismatching_nodes_dict
        }

    # Information about all changed nodes in puppet
    changed_nodes_list = puppetdb_results['changed_nodes']
    _changed_nodes_dict = {
        item['certname']: item for item in changed_nodes_list if
        item['certname'] not in _unreported_nodes_dict and
        item['certname'] not in _mismatching_nodes_dict
        }

    # Information about all noop nodes in puppet
    noop_nodes_list = puppetdb_results['noop_nodes']
    _noop_nodes_dict = {
        item['certname']: item for item in noop_nodes_list if
        item['certname'] not in _unreported_nodes_dict and
        item['certname'] not in _mismatching_nodes_dict
        }

    _default_merge = {
        'failures': 0,
        'skips': 0,
        'successes': 0,
        'noops': 0
    }

    unreported_nodes_list = [merge_two_dicts(item, event_dict.get(item['certname'], _default_merge))
                             for item in _unreported_nodes_dict.values()
                             if item['certname'] in event_dict]

    mismatching_node_list = [merge_two_dicts(item, event_dict.get(item['certname'], _default_merge))
                             for item in _mismatching_nodes_dict.values()
                             if item['certname'] in event_dict]

    failed_node_list = [merge_two_dicts(item, event_dict.get(item['certname'], _default_merge))
                        for item in _failed_nodes_dict.values()
                        if item['certname'] in event_dict]

    changed_node_list = [merge_two_dicts(item, event_dict.get(item['certname'], _default_merge))
                         for item in _changed_nodes_dict.values()
                         if item['certname'] in event_dict]

    noop_node_list = [merge_two_dicts(item, event_dict.get(item['certname'], _default_merge))
                      for item in _noop_nodes_dict.values()
                      if item['certname'] in event_dict]

    c = dt.datetime.utcnow()
    print("Data extraction and dictify total: %s " % (c - b).total_seconds())

    print('# Total nodes found')
    print('count - all_nodes: %s' % len(all_nodes_dict))
    # print('count - failed_nodes: %s' % len(failed_nodes_dict))
    # print('count - unreported_nodes: %s' % len(unreported_nodes_))
    print('count - changed_nodes: %s' % len(changed_nodes_list))
    # print('count - noop_nodes: %s' % len(noop_nodes_dict))
    # print('count - mismatching_nodes: %s' % len(mismatching_nodes_dict))
    print("Total time for all ops: %s " % (c - a).total_seconds())
    print('---')

    return HttpResponse(json.dumps({'data': unreported_nodes_list}, indent=2), content_type="application/json")

    # context['node_list'] = merged_nodes_list
    # context['selected_view'] = dashboard_show
    # context['population'] = puppet_population
    # context['total_resource'] = total_resources['Value']
    # context['avg_resource'] = "{:.2f}".format(avg_resource_node['Value'])
    # context['failed_nodes'] = node_fail_count
    # context['changed_nodes'] = node_change_count
    # context['unreported_nodes'] = node_unreported_count
    # context['mismatching_timestamps'] = node_off_timestamps_count
    # context['pending_nodes'] = node_pending_count
