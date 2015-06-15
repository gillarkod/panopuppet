__author__ = 'etaklar'

from pano.puppetdb.puppetdb import api_get as pdb_api_get
from pano.puppetdb.puppetdb import mk_puppetdb_query
import queue
from threading import Thread
from pano.puppetdb.puppetdb import get_server


def summary_of_events(events_hash):
    summary = {
        'classes_failure': {},
        'classes_noop': {},
        'classes_success': {},
        'classes_skipped': {},
        'classes_total': 0,

        'nodes_failure': {},
        'nodes_noop': {},
        'nodes_success': {},
        'nodes_skipped': {},
        'nodes_total': 0,

        'resources_failure': {},
        'resources_noop': {},
        'resources_success': {},
        'resources_skipped': {},
        'resources_total': 0,

        'types_failure': {},
        'types_noop': {},
        'types_success': {},
        'types_skipped': {},
        'types_total': 0,
    }

    def sort_events(all_events, threads=2):
        if type(threads) != int:
            threads = 6
        jobs_q = queue.Queue()
        out_q = queue.Queue()

        def db_threaded_requests(i, q):
            while True:
                t_event = q.get()
                if t_event['status'] == 'success':
                    # Classes
                    if not t_event['containing-class'] in summary['classes_success']:
                        summary['classes_success'][t_event['containing-class']] = 1
                    else:
                        summary['classes_success'][t_event['containing-class']] += 1
                    # Nodes
                    if not t_event['certname'] in summary['nodes_success']:
                        summary['nodes_success'][t_event['certname']] = 1
                    else:
                        summary['nodes_success'][t_event['certname']] += 1
                    # Resources
                    if not t_event['resource-title'] in summary['resources_success']:
                        summary['resources_success'][t_event['resource-title']] = 1
                    else:
                        summary['resources_success'][t_event['resource-title']] += 1
                    # Types
                    if not t_event['resource-type'] in summary['types_success']:
                        summary['types_success'][t_event['resource-type']] = 1
                    else:
                        summary['types_success'][t_event['resource-type']] += 1

                if t_event['status'] == 'noop':
                    # Classes
                    if not t_event['containing-class'] in summary['classes_noop']:
                        summary['classes_noop'][t_event['containing-class']] = 1
                    else:
                        summary['classes_noop'][t_event['containing-class']] += 1
                    # Nodes
                    if not t_event['certname'] in summary['nodes_noop']:
                        summary['nodes_noop'][t_event['certname']] = 1
                    else:
                        summary['nodes_noop'][t_event['certname']] += 1
                    # Resources
                    if not t_event['resource-title'] in summary['resources_noop']:
                        summary['resources_noop'][t_event['resource-title']] = 1
                    else:
                        summary['resources_noop'][t_event['resource-title']] += 1
                    # Types
                    if not t_event['resource-type'] in summary['types_noop']:
                        summary['types_noop'][t_event['resource-type']] = 1
                    else:
                        summary['types_noop'][t_event['resource-type']] += 1

                if t_event['status'] == 'failure':
                    # Classes
                    if not t_event['containing-class'] in summary['classes_failure']:
                        summary['classes_failure'][t_event['containing-class']] = 1
                    else:
                        summary['classes_failure'][t_event['containing-class']] += 1
                    # Nodes
                    if not t_event['certname'] in summary['nodes_failure']:
                        summary['nodes_failure'][t_event['certname']] = 1
                    else:
                        summary['nodes_failure'][t_event['certname']] += 1
                    # Resources
                    if not t_event['resource-title'] in summary['resources_failure']:
                        summary['resources_failure'][t_event['resource-title']] = 1
                    else:
                        summary['resources_failure'][t_event['resource-title']] += 1
                    # Types
                    if not t_event['resource-type'] in summary['types_failure']:
                        summary['types_failure'][t_event['resource-type']] = 1
                    else:
                        summary['types_failure'][t_event['resource-type']] += 1

                if t_event['status'] == 'skipped':
                    # Classes
                    if not t_event['containing-class'] in summary['classes_skipped']:
                        summary['classes_skipped'][t_event['containing-class']] = 1
                    else:
                        summary['classes_skipped'][t_event['containing-class']] += 1
                    # Nodes
                    if not t_event['certname'] in summary['nodes_skipped']:
                        summary['nodes_skipped'][t_event['certname']] = 1
                    else:
                        summary['nodes_skipped'][t_event['certname']] += 1
                    # Resources
                    if not t_event['resource-title'] in summary['resources_skipped']:
                        summary['resources_skipped'][t_event['resource-title']] = 1
                    else:
                        summary['resources_skipped'][t_event['resource-title']] += 1
                    # Types
                    if not t_event['resource-type'] in summary['types_skipped']:
                        summary['types_skipped'][t_event['resource-type']] = 1
                    else:
                        summary['types_skipped'][t_event['resource-type']] += 1
                out_q.put(i)
                q.task_done()

        for i in range(threads):
            worker = Thread(target=db_threaded_requests, args=(i, jobs_q))
            worker.setDaemon(True)
            worker.start()

        for single_event in all_events:
            jobs_q.put(single_event)
        jobs_q.join()

        while True:
            try:
                out_q.get_nowait()
            except queue.Empty:
                break

    sort_events(events_hash)
    # count totals
    # Classes
    summary['classes_total'] = len(summary['classes_success']) + len(summary['classes_noop']) + len(
        summary['classes_failure']) + len(summary['classes_skipped'])
    # Nodes
    summary['nodes_total'] = len(summary['nodes_success']) + len(summary['nodes_noop']) + len(
        summary['nodes_failure']) + len(summary['nodes_skipped'])
    # resource
    summary['resources_total'] = len(summary['resources_success']) + len(summary['resources_noop']) + len(
        summary['resources_failure']) + len(summary['resources_skipped'])
    # types
    summary['types_total'] = len(summary['types_success']) + len(summary['types_noop']) + len(
        summary['types_failure']) + len(summary['types_skipped'])

    return summary


def get_events_summary(request, timespan='latest'):
    if timespan == 'latest':
        events_params = {
            'query':
                {
                    1: '["and",["=","latest-report?",true],["in", "certname",["extract", "certname",["select-nodes",["null?","deactivated",true]]]]]'
                },
        }
    source_url, source_certs, source_verify = get_server(request)
    events = pdb_api_get(
        api_url=source_url,
        cert=source_certs,
        verify=source_verify,
        path='events/',
        api_version='v4',
        params=mk_puppetdb_query(events_params))
    summary = summary_of_events(events)
    return summary


def get_report(key, value, request):
    source_url, source_certs, source_verify = get_server(request)
    # If key is any of the below, all is good!
    allowed_keys = ['certname', 'resource-title', 'resource-type', 'containing-class']
    if key in allowed_keys:
        pass
    # If key does not match above the default will be shown
    else:
        key = 'containing-class'

    events_params = {
        'query':
            {
                'operator': 'and',
                1: '["=","' + key + '","' + value + '"]',
                2: '["=","latest-report?",true]'
            },
    }
    results = pdb_api_get(
        api_url=source_url,
        cert=source_certs,
        verify=source_verify,
        path='events/',
        api_version='v4',
        params=mk_puppetdb_query(events_params),
    )
    return results
