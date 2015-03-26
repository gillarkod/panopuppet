__author__ = 'etaklar'

from pano.puppetdb.pdbutils import json_to_datetime, is_unreported
from pano.settings import PUPPET_RUN_INTERVAL
from datetime import timedelta


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
    def sort_table(table, col=0, order=False):
        return sorted(table, reverse=order, key=lambda field: field[col])

    def check_failed_compile(report_timestamp, fact_timestamp, catalog_timestamp):
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

        if elapsed_catalog > timedelta(minutes=PUPPET_RUN_INTERVAL / 2):
            return True
        elif elapsed_report > timedelta(minutes=PUPPET_RUN_INTERVAL / 2):
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
        sortbycol = sortables.get(sortby, 5)
    else:
        sortbycol = 2

    merged_list = []
    for node in node_dict:
        found_node = False
        for status in status_dict:
            if node['name'] == status['subject']['title']:
                found_node = True
                if get_status == "all":
                    merged_list.append((
                        node['name'],
                        node['catalog_timestamp'] or '',
                        node['report_timestamp'] or '',
                        node['facts_timestamp'] or '',
                        status['successes'],
                        status['noops'],
                        status['failures'],
                        status['skips'],
                    ))
                elif get_status == "noop" and status['noops'] > 0:
                    merged_list.append((
                        node['name'],
                        node['catalog_timestamp'] or '',
                        node['report_timestamp'] or '',
                        node['facts_timestamp'] or '',
                        status['successes'],
                        status['noops'],
                        status['failures'],
                        status['skips'],
                    ))
                elif get_status == "failed" and status['failures'] > 0:
                    merged_list.append((
                        node['name'],
                        node['catalog_timestamp'] or '',
                        node['report_timestamp'] or '',
                        node['facts_timestamp'] or '',
                        status['successes'],
                        status['noops'],
                        status['failures'],
                        status['skips'],
                    ))
                elif get_status == "changed":
                    merged_list.append((
                        node['name'],
                        node['catalog_timestamp'] or '',
                        node['report_timestamp'] or '',
                        node['facts_timestamp'] or '',
                        status['successes'],
                        status['noops'],
                        status['failures'],
                        status['skips'],
                    ))
                elif get_status == "unreported":
                    if is_unreported(node['report_timestamp']):
                        merged_list.append((
                            node['name'],
                            node['catalog_timestamp'] or '',
                            node['report_timestamp'] or '',
                            node['facts_timestamp'] or '',
                            status['successes'],
                            status['noops'],
                            status['failures'],
                            status['skips'],
                        ))
                elif get_status == "failed_catalogs":
                    if check_failed_compile(report_timestamp=node.get('report_timestamp', None),
                                            fact_timestamp=node.get('facts_timestamp', None),
                                            catalog_timestamp=node.get('catalog_timestamp', None)):
                        merged_list.append((
                            node['name'],
                            node['catalog_timestamp'] or '',
                            node['report_timestamp'] or '',
                            node['facts_timestamp'] or '',
                            status['successes'],
                            status['noops'],
                            status['failures'],
                            status['skips'],
                        ))
                break

        # We can assume that the node has not changed if its not found in the
        # event-counts output.
        if found_node is False and get_status == "all":
            merged_list.append((
                node['name'],
                node['catalog_timestamp'] or '',
                node['report_timestamp'] or '',
                node['facts_timestamp'] or '',
                0,
                0,
                0,
                0,
            ))
        elif found_node is False and get_status == "unreported":
            if is_unreported(node['report_timestamp']):
                merged_list.append((
                    node['name'],
                    node['catalog_timestamp'] or '',
                    node['report_timestamp'] or '',
                    node['facts_timestamp'] or '',
                    0,
                    0,
                    0,
                    0,
                ))
        elif found_node is False and get_status == "failed_catalogs":
            if check_failed_compile(report_timestamp=node.get('report_timestamp', None),
                                    fact_timestamp=node.get('facts_timestamp', None),
                                    catalog_timestamp=node.get('catalog_timestamp', None)):
                merged_list.append((
                    node['name'],
                    node['catalog_timestamp'] or '',
                    node['report_timestamp'] or '',
                    node['facts_timestamp'] or '',
                    0,
                    0,
                    0,
                    0,
                ))
    if sort:
        return sort_table(merged_list, order=asc, col=sortbycol)
    return merged_list
