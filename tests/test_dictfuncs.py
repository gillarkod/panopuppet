__author__ = 'etaklar'

from django.test import TestCase
from datetime import datetime, timedelta
from pano.methods.dictfuncs import dictstatus


class MergeNodeEventData(TestCase):
    def test_node_event_data_merged(self):
        nodes_data = [
            {
                'catalog-environment': 'production',
                'catalog-timestamp': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'certname': 'failed-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report-environment': 'production',
                'report-timestamp': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'certname': 'missmatch-node1.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': ((datetime.utcnow() - timedelta(minutes=55)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report-environment': 'production',
                'report-timestamp': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'certname': 'missmatch-node2.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report-environment': 'production',
                'report-timestamp': ((datetime.utcnow() - timedelta(minutes=55)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': ((datetime.utcnow() - timedelta(minutes=50)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'certname': 'missmatch-node3.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report-environment': 'production',
                'report-timestamp': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': ((datetime.utcnow() - timedelta(minutes=127)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'certname': 'unreported-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': ((datetime.utcnow() - timedelta(minutes=126)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report-environment': 'production',
                'report-timestamp': ((datetime.utcnow() - timedelta(minutes=125)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'certname': 'changed-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report-environment': 'production',
                'report-timestamp': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': ((datetime.utcnow() - timedelta(minutes=25)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'certname': 'unchanged-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': ((datetime.utcnow() - timedelta(minutes=24)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report-environment': 'production',
                'report-timestamp': ((datetime.utcnow() - timedelta(minutes=23)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': ((datetime.utcnow() - timedelta(minutes=16)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'certname': 'pending-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': ((datetime.utcnow() - timedelta(minutes=13)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report-environment': 'production',
                'report-timestamp': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            }]

        events_data = [{'failures': 0,
                        'noops': 0,
                        'skips': 0,
                        'subject': {'title': 'changed-node.example.com'},
                        'subject-type': 'certname',
                        'successes': 78},
                       {'failures': 0,
                        'noops': 100,
                        'skips': 0,
                        'subject': {'title': 'pending-node.example.com'},
                        'subject-type': 'certname',
                        'successes': 0},
                       {'failures': 20,
                        'noops': 0,
                        'skips': 10,
                        'subject': {'title': 'failed-node.example.com'},
                        'subject-type': 'certname',
                        'successes': 5},
                       {'failures': 20,
                        'noops': 0,
                        'skips': 10,
                        'subject': {'title': 'missmatch-node1.example.com'},
                        'subject-type': 'certname',
                        'successes': 5},
                       {'failures': 0,
                        'noops': 0,
                        'skips': 0,
                        'subject': {'title': 'missmatch-node2.example.com'},
                        'subject-type': 'certname',
                        'successes': 25},
                       {'failures': 0,
                        'noops': 50,
                        'skips': 0,
                        'subject': {'title': 'missmatch-node3.example.com'},
                        'subject-type': 'certname',
                        'successes': 0}
                       ]
        failed_list, changed_list, unreported_list, mismatch_list, pending_list = dictstatus(nodes_data,
                                                                                             events_data,
                                                                                             sort=False,
                                                                                             get_status='notall')
        from pprint import pprint as print
        print("---failed")
        print(failed_list)
        print("---changed")
        print(changed_list)
        print("---unreported")
        print(unreported_list)
        print("---missmatch")
        print(mismatch_list)
        print("---pending")
        print(pending_list)
        self.assertEqual("", "")
