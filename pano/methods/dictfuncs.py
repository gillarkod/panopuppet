__author__ = 'etaklar'

from pano.puppetdb.pdbutils import json_to_datetime, is_unreported
from pano.settings import PUPPET_RUN_INTERVAL
from datetime import timedelta
from django.template import defaultfilters as filters
from django.utils.timezone import localtime



def sort_table(table, col=0, order=False):
    return sorted(table, reverse=order, key=lambda field: field[col])


def dictstatus(node_dict, status_dict, sort=True, sortby=None, asc=False, get_status="all", puppet_run_time=PUPPET_RUN_INTERVAL):
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
                             puppet_run_interval=puppet_run_time):
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

    sortables = {
        'certname': 0,
        'catalog_timestamp': 1,
        'report_timestamp': 2,
        'facts_timestamp': 3,
        'successes': 4,
        'noops': 5,
        'failures': 6,
        'skips': 7,
    }

    if sortby:
        # Sort by the field recieved, if valid field was not supplied, fallback
        # to report
        sortbycol = sortables.get(sortby, 2)
    else:
        sortbycol = 2

    # if sortbycol is 4, 5, 6 or 7 ( a different list creation method must be used.

    merged_list = []
    failed_list = []
    unreported_list = []
    changed_list = []
    pending_list = []
    mismatch_list = []

    def append_list(n_data, s_data, m_list):
        if type(n_data) is not dict or type(s_data) is not dict and type(m_list) is not list:
            raise ValueError('Incorrect type given as input. Expects n_data, s_data as dict and m_list as list.')
        m_list.append((
            n_data['certname'],
            filters.date(localtime(json_to_datetime(n_data['catalog_timestamp'])), 'Y-m-d H:i:s') if n_data['catalog_timestamp'] is not None else '',
            filters.date(localtime(json_to_datetime(n_data['report_timestamp'])), 'Y-m-d H:i:s') if n_data['report_timestamp'] is not None else '',
            filters.date(localtime(json_to_datetime(n_data['facts_timestamp'])), 'Y-m-d H:i:s') if n_data['facts_timestamp'] is not None else '',
            s_data.get('successes', 0),
            s_data.get('noops', 0),
            s_data.get('failures', 0),
            s_data.get('skips', 0),
        ))
        return m_list
    # if sort field is certname or catalog/report/facts_timestamp then we will sort this way
    # or if the get_status is set to "not_all" indicating that the dashboard wants info.
    if get_status != 'all':
        for node in node_dict:
            found_node = False
            for status in status_dict:
                if node['certname'] == status['subject']['title']:
                    found_node = True
                    # If the node has failures
                    if status['failures'] > 0:
                        failed_list = append_list(node, status, failed_list)
                    if check_failed_compile(report_timestamp=node.get('report_timestamp', None),
                                            fact_timestamp=node.get('facts_timestamp', None),
                                            catalog_timestamp=node.get('catalog_timestamp', None)):
                        mismatch_list = append_list(node, status, mismatch_list)
                    # If the node is unreported
                    if is_unreported(node['report_timestamp']):
                        unreported_list = append_list(node, status, unreported_list)
                    # If the node has noops
                    if status['noops'] > 0 \
                            and status['successes'] == 0 \
                            and status['failures'] == 0 \
                            and status['skips'] == 0:
                        pending_list = append_list(node, status, pending_list)
                    # The node was found in the events list so it has to have changed
                    changed_list = append_list(node, status, changed_list)
                # Found the node in events list so we can break this loop
                    break
            if found_node is False:
                # If the node is unreported
                if is_unreported(node['report_timestamp']):
                    unreported_list = append_list(node, dict(), unreported_list)
                if check_failed_compile(report_timestamp=node.get('report_timestamp', None),
                                        fact_timestamp=node.get('facts_timestamp', None),
                                        catalog_timestamp=node.get('catalog_timestamp', None)):
                    mismatch_list = append_list(node, dict(), mismatch_list)
    elif sortbycol <= 3 and get_status == 'all':
        for node in node_dict:
            found_node = False
            for status in status_dict:
                if node['certname'] == status['subject']['title']:
                    found_node = True
                    merged_list = append_list(node, status, merged_list)
                    # Found the node in events list so we can break this loop
                    break
            if found_node is False:
                merged_list = append_list(node, dict(), merged_list)
    # Only used when orderby is a status field.
    elif sortbycol >= 4 and get_status == 'all':
        for status in status_dict:
            found_node = False
            for node in node_dict:
                if node['certname'] == status['subject']['title']:
                    found_node = True
                    merged_list = append_list(node, status, merged_list)
                    break

    # Sort the lists if sort is True
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
