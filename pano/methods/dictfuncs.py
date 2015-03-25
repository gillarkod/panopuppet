__author__ = 'etaklar'

import pano.puppetdb.pdbutils


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
                    if pano.puppetdb.pdbutils.is_unreported(node['report_timestamp']):
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
            if pano.puppetdb.pdbutils.is_unreported(node['report_timestamp']):
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
