__author__ = 'etaklar'

from pano.puppetdb.pdbutils import json_to_datetime, is_unreported
from pano.settings import PUPPET_RUN_INTERVAL
from datetime import timedelta


def sort_table(table, col=0, order=False):
    return sorted(table, reverse=order, key=lambda field: field[col])


def dictstatus(node_dict, status_dict, sort=True, sortby=None, asc=False, get_status="all"):
    """
    :param node_dict: dict
    :param status_dict: dict
    :param sortby: Takes a field name to sort by 'certname', 'latestCatalog', 'latestReport', 'latestFacts', 'success', 'noop', 'failure', 'skipped'
    :param get_status: Status type to return. all, changed, failed, unreported, noops
    :return: tuple(tuple,tuple)

    node_dict input:
    [
        {
            "name": <string>,
            "deactivated": <timestamp>,
            "catalog_timestamp": <timestamp>,
            "facts_timestamp": <timestamp>,
            "report_timestamp": <timestamp>
        },
    ]
    --------------------------------
    status_dict input:
    [
        {
            "subject-type": "certname",
            "subject": { "title": "foo.local" },
            "failures": 0,
            "successes": 2,
            "noops": 0,
           "skips": 1
        },
    ]
    """

    # The merged_list tuple should look like this.
    # (
    # ('certname', 'latestCatalog', 'latestReport', 'latestFacts', 'success', 'noop', 'failure', 'skipped'),
    # )
    def check_failed_compile(report_timestamp,
                             fact_timestamp,
                             catalog_timestamp,
                             puppet_run_interval=PUPPET_RUN_INTERVAL):
        """
        :param report_timestamp: str
        :param fact_timestamp: str
        :param catalog_timestamp: str
        :return: Bool
        Returns False if the compiled run has not failed
        Returns True if the compiled run has failed
        """
        if report_timestamp is None or catalog_timestamp is None or fact_timestamp is None:
            return True
        # check if the fact report is older than puppet_run_time by double the run time
        report_time = json_to_datetime(report_timestamp)
        fact_time = json_to_datetime(fact_timestamp)
        catalog_time = json_to_datetime(catalog_timestamp)

        # Report time, fact time and catalog time should all be run within (PUPPET_RUN_INTERVAL / 2)
        # minutes of each other

        # Time elapsed between fact time and catalog time
        elapsed_catalog = catalog_time - fact_time
        # Time elapsed between fact time and report time
        elapsed_report = report_time - fact_time

        if elapsed_catalog > timedelta(minutes=puppet_run_interval / 2):
            return True
        elif elapsed_report > timedelta(minutes=puppet_run_interval / 2):
            return True
        else:
            return False

    sortables = {
        'certname': 0,
        'latestCatalog': 1,
        'latestReport': 2,
        'latestFacts': 3,
        'success': 4,
        'noop': 5,
        'failure': 6,
        'skipped': 7,
    }

    if sortby:
        # Sort by the field recieved, if valid field was not supplied, fallback
        # to report
        sortbycol = sortables.get(sortby, 2)
    else:
        sortbycol = 2

    merged_list = []
    failed_list = []
    unreported_list = []
    changed_list = []
    pending_list = []
    mismatch_list = []

    for node in node_dict:
        found_node = False
        for status in status_dict:
            if node['certname'] == status['subject']['title']:
                found_node = True
                if get_status == "all":
                    merged_list.append((
                        node['certname'],
                        node['catalog-timestamp'] or '',
                        node['report-timestamp'] or '',
                        node['facts-timestamp'] or '',
                        status['successes'],
                        status['noops'],
                        status['failures'],
                        status['skips'],
                    ))
                else:
                    # If the node has failures
                    if status['failures'] > 0:
                        failed_list.append((
                            node['certname'],
                            node['catalog-timestamp'] or '',
                            node['report-timestamp'] or '',
                            node['facts-timestamp'] or '',
                            status['successes'],
                            status['noops'],
                            status['failures'],
                            status['skips'],
                        ))
                    if check_failed_compile(report_timestamp=node.get('report-timestamp', None),
                                            fact_timestamp=node.get('facts-timestamp', None),
                                            catalog_timestamp=node.get('catalog-timestamp', None)):
                        mismatch_list.append((
                            node['certname'],
                            node['catalog-timestamp'] or '',
                            node['report-timestamp'] or '',
                            node['facts-timestamp'] or '',
                            status['successes'],
                            status['noops'],
                            status['failures'],
                            status['skips'],
                        ))
                    # If the node is unreported
                    if is_unreported(node['report-timestamp']):
                        unreported_list.append((
                            node['certname'],
                            node['catalog-timestamp'] or '',
                            node['report-timestamp'] or '',
                            node['facts-timestamp'] or '',
                            status['successes'],
                            status['noops'],
                            status['failures'],
                            status['skips'],
                        ))
                    # If the node has noops
                    if status['noops'] > 0 \
                            and status['successes'] == 0 \
                            and status['failures'] == 0 \
                            and status['skips'] == 0:
                        pending_list.append((
                            node['certname'],
                            node['catalog-timestamp'] or '',
                            node['report-timestamp'] or '',
                            node['facts-timestamp'] or '',
                            status['successes'],
                            status['noops'],
                            status['failures'],
                            status['skips'],
                        ))
                    # The node was found in the events list so it has to have changed
                    changed_list.append((
                        node['certname'],
                        node['catalog-timestamp'] or '',
                        node['report-timestamp'] or '',
                        node['facts-timestamp'] or '',
                        status['successes'],
                        status['noops'],
                        status['failures'],
                        status['skips'],
                    ))
                # Found the node in events list so we can break this loop
                break
        if found_node is False:
            if get_status == "all":
                merged_list.append((
                    node['certname'],
                    node['catalog-timestamp'] or '',
                    node['report-timestamp'] or '',
                    node['facts-timestamp'] or '',
                    0,
                    0,
                    0,
                    0,
                ))
            else:
                # If the node is unreported
                if is_unreported(node['report-timestamp']):
                    unreported_list.append((
                        node['certname'],
                        node['catalog-timestamp'] or '',
                        node['report-timestamp'] or '',
                        node['facts-timestamp'] or '',
                        0,
                        0,
                        0,
                        0,
                    ))
                if check_failed_compile(report_timestamp=node.get('report-timestamp', None),
                                        fact_timestamp=node.get('facts-timestamp', None),
                                        catalog_timestamp=node.get('catalog-timestamp', None)):
                    mismatch_list.append((
                        node['certname'],
                        node['catalog-timestamp'] or '',
                        node['report-timestamp'] or '',
                        node['facts-timestamp'] or '',
                        0,
                        0,
                        0,
                        0,
                    ))

    if sort and get_status == 'all':
        return sort_table(merged_list, order=asc, col=sortbycol)
    elif sort and get_status != 'all':
        sorted_unreported_list = sort_table(unreported_list, order=asc, col=sortbycol)
        sorted_changed_list = sort_table(changed_list, order=asc, col=sortbycol)
        sorted_failed_list = sort_table(failed_list, order=asc, col=sortbycol)
        sorted_mismatch_list = sort_table(mismatch_list, order=asc, col=sortbycol)
        sorted_pending_list = sort_table(pending_list, order=asc, col=sortbycol)
        return sorted_failed_list, \
               sorted_changed_list, \
               sorted_unreported_list, \
               sorted_mismatch_list, \
               sorted_pending_list

    if get_status == 'all':
        return merged_list
    else:
        return failed_list, changed_list, unreported_list, mismatch_list, pending_list
