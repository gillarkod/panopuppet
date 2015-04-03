__author__ = 'etaklar'

from pano.puppetdb.puppetdb import api_get as pdb_api_get
from pano.puppetdb.puppetdb import mk_puppetdb_query


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

    for event in events_hash:
        if event['status'] == 'success':
            # Classes
            if not event['containing-class'] in summary['classes_success']:
                summary['classes_success'][event['containing-class']] = 1
            else:
                summary['classes_success'][event['containing-class']] += 1
            # Nodes
            if not event['certname'] in summary['nodes_success']:
                summary['nodes_success'][event['certname']] = 1
            else:
                summary['nodes_success'][event['certname']] += 1
            # Resources
            if not event['resource-title'] in summary['resources_success']:
                summary['resources_success'][event['resource-title']] = 1
            else:
                summary['resources_success'][event['resource-title']] += 1
            # Types
            if not event['resource-type'] in summary['types_success']:
                summary['types_success'][event['resource-type']] = 1
            else:
                summary['types_success'][event['resource-type']] += 1

        if event['status'] == 'noop':
            # Classes
            if not event['containing-class'] in summary['classes_noop']:
                summary['classes_noop'][event['containing-class']] = 1
            else:
                summary['classes_noop'][event['containing-class']] += 1
            # Nodes
            if not event['certname'] in summary['nodes_noop']:
                summary['nodes_noop'][event['certname']] = 1
            else:
                summary['nodes_noop'][event['certname']] += 1
            # Resources
            if not event['resource-title'] in summary['resources_noop']:
                summary['resources_noop'][event['resource-title']] = 1
            else:
                summary['resources_noop'][event['resource-title']] += 1
            # Types
            if not event['resource-type'] in summary['types_noop']:
                summary['types_noop'][event['resource-type']] = 1
            else:
                summary['types_noop'][event['resource-type']] += 1

        if event['status'] == 'failure':
            # Classes
            if not event['containing-class'] in summary['classes_failure']:
                summary['classes_failure'][event['containing-class']] = 1
            else:
                summary['classes_failure'][event['containing-class']] += 1
            # Nodes
            if not event['certname'] in summary['nodes_failure']:
                summary['nodes_failure'][event['certname']] = 1
            else:
                summary['nodes_failure'][event['certname']] += 1
            # Resources
            if not event['resource-title'] in summary['resources_failure']:
                summary['resources_failure'][event['resource-title']] = 1
            else:
                summary['resources_failure'][event['resource-title']] += 1
            # Types
            if not event['resource-type'] in summary['types_failure']:
                summary['types_failure'][event['resource-type']] = 1
            else:
                summary['types_failure'][event['resource-type']] += 1

        if event['status'] == 'skipped':
            # Classes
            if not event['containing-class'] in summary['classes_skipped']:
                summary['classes_skipped'][event['containing-class']] = 1
            else:
                summary['classes_skipped'][event['containing-class']] += 1
            # Nodes
            if not event['certname'] in summary['nodes_skipped']:
                summary['nodes_skipped'][event['certname']] = 1
            else:
                summary['nodes_skipped'][event['certname']] += 1
            # Resources
            if not event['resource-title'] in summary['resources_skipped']:
                summary['resources_skipped'][event['resource-title']] = 1
            else:
                summary['resources_skipped'][event['resource-title']] += 1
            # Types
            if not event['resource-type'] in summary['types_skipped']:
                summary['types_skipped'][event['resource-type']] = 1
            else:
                summary['types_skipped'][event['resource-type']] += 1
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


def get_events_summary(timespan='latest'):
    if timespan == 'latest':
        events_params = {
            'query':
                {
                    1: '["=","latest-report?",true]'
                },
        }
    events = pdb_api_get(path='events/',
                         api_version='v3',
                         params=mk_puppetdb_query(
                             events_params))
    summary = summary_of_events(events)
    return summary

