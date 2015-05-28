__author__ = 'etaklar'

from django.test import TestCase
from datetime import datetime, timedelta
from pano.methods.dictfuncs import dictstatus
from django.template import defaultfilters as filters
from django.utils.timezone import localtime
from pano.puppetdb.pdbutils import json_to_datetime


class MergeNodeEventData(TestCase):
    def test_nodes_seperated_data(self):
        nodes_timestamps = {
            'failed-node': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'missmatch-node1': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=55)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'missmatch-node2': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=55)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'missmatch-node3': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=50)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'unreported-node': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=127)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=126)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=125)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'changed-node': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'unchanged-node': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=25)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=24)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=23)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'pending-node': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=16)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=13)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
        }

        nodes_data = [
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['failed-node']['catalog'],
                'certname': 'failed-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['failed-node']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['failed-node']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['missmatch-node1']['catalog'],
                'certname': 'missmatch-node1.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['missmatch-node1']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['missmatch-node1']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['missmatch-node2']['catalog'],
                'certname': 'missmatch-node2.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['missmatch-node2']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['missmatch-node2']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['missmatch-node3']['catalog'],
                'certname': 'missmatch-node3.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['missmatch-node3']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['missmatch-node3']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['unreported-node']['catalog'],
                'certname': 'unreported-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['unreported-node']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['unreported-node']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['changed-node']['catalog'],
                'certname': 'changed-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['changed-node']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['changed-node']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['unchanged-node']['catalog'],
                'certname': 'unchanged-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['unchanged-node']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['unchanged-node']['report'],
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['pending-node']['catalog'],
                'certname': 'pending-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['pending-node']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['pending-node']['report'],
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
        failed_list, changed_list, unreported_list, missmatch_list, pending_list = dictstatus(nodes_data,
                                                                                              events_data,
                                                                                              sort=False,
                                                                                              get_status='notall')
        # ('certname', 'latestCatalog', 'latestReport', 'latestFacts', 'success', 'noop', 'failure', 'skipped')
        failed_expected = [(
            'failed-node.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['failed-node']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['failed-node']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['failed-node']['facts'])),
                'Y-m-d H:i:s'),
            5, 0, 20, 10), (
            'missmatch-node1.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['facts'])),
                'Y-m-d H:i:s'),
            5, 0, 20, 10)]

        changed_expected = [(
            'failed-node.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['failed-node']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['failed-node']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['failed-node']['facts'])),
                'Y-m-d H:i:s'),
            5, 0, 20, 10), (
            'missmatch-node1.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['facts'])),
                'Y-m-d H:i:s'),
            5, 0, 20, 10), (
            'missmatch-node2.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node2']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node2']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node2']['facts'])),
                'Y-m-d H:i:s'),
            25, 0, 0, 0), (
            'missmatch-node3.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['facts'])),
                'Y-m-d H:i:s'),
            0, 50, 0, 0), (
            'changed-node.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['changed-node']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['changed-node']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['changed-node']['facts'])),
                'Y-m-d H:i:s'),
            78, 0, 0, 0), (
            'pending-node.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['pending-node']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['pending-node']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['pending-node']['facts'])),
                'Y-m-d H:i:s'),
            0, 100, 0, 0)]

        unreported_expected = [(
            'unreported-node.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['unreported-node']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['unreported-node']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['unreported-node']['facts'])),
                'Y-m-d H:i:s'),
            0, 0, 0, 0)]

        missmatch_expected = [(
            'missmatch-node1.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['facts'])),
                'Y-m-d H:i:s'),
            5, 0, 20, 10), (
            'missmatch-node2.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node2']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node2']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node2']['facts'])),
                'Y-m-d H:i:s'),
            25, 0, 0, 0), (
            'missmatch-node3.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['facts'])),
                'Y-m-d H:i:s'),
            0, 50, 0, 0)]

        pending_expected = [(
            'missmatch-node3.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['facts'])),
                'Y-m-d H:i:s'),
            0, 50, 0, 0), (
            'pending-node.example.com',
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['pending-node']['catalog'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['pending-node']['report'])),
                'Y-m-d H:i:s'),
            filters.date(
                localtime(json_to_datetime(nodes_timestamps['pending-node']['facts'])),
                'Y-m-d H:i:s'),
            0, 100, 0, 0)]
        # failed_list, changed_list, unreported_list, mismatch_list, pending_list
        if failed_list != failed_expected:
            self.fail(msg='Failed list does not match expectations.')
        if changed_list != changed_expected:
            self.fail(msg='Changed list does not match expectations.')
        if unreported_list != unreported_expected:
            self.fail(msg='Unreported list does not match expectations.')
        if missmatch_list != missmatch_expected:
            self.fail(msg='Missmatching list does not match expectations.')
        if pending_list != pending_expected:
            self.fail(msg='Pending list does not match expectations.')
        self.assertTrue(True)

    def test_nodes_merged_data(self):
        nodes_timestamps = {
            'failed-node': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'missmatch-node1': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=55)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'missmatch-node2': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=55)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'missmatch-node3': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=50)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'unreported-node': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=127)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=126)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=125)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'changed-node': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=11)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=9)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'unchanged-node': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=25)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=24)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=23)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
            'pending-node': {
                'catalog': ((datetime.utcnow() - timedelta(minutes=16)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'facts': ((datetime.utcnow() - timedelta(minutes=13)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
                'report': ((datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            },
        }

        nodes_data = [
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['failed-node']['catalog'],
                'certname': 'failed-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['failed-node']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['failed-node']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['missmatch-node1']['catalog'],
                'certname': 'missmatch-node1.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['missmatch-node1']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['missmatch-node1']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['missmatch-node2']['catalog'],
                'certname': 'missmatch-node2.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['missmatch-node2']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['missmatch-node2']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['missmatch-node3']['catalog'],
                'certname': 'missmatch-node3.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['missmatch-node3']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['missmatch-node3']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['unreported-node']['catalog'],
                'certname': 'unreported-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['unreported-node']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['unreported-node']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['changed-node']['catalog'],
                'certname': 'changed-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['changed-node']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['changed-node']['report']
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['unchanged-node']['catalog'],
                'certname': 'unchanged-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['unchanged-node']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['unchanged-node']['report'],
            },
            {
                'catalog-environment': 'production',
                'catalog-timestamp': nodes_timestamps['pending-node']['catalog'],
                'certname': 'pending-node.example.com',
                'deactivated': None,
                'facts-environment': 'production',
                'facts-timestamp': nodes_timestamps['pending-node']['facts'],
                'report-environment': 'production',
                'report-timestamp': nodes_timestamps['pending-node']['report'],
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
        merged_list = dictstatus(nodes_data,
                                 events_data,
                                 sort=False,
                                 get_status='all')
        # ('certname', 'latestCatalog', 'latestReport', 'latestFacts', 'success', 'noop', 'failure', 'skipped')
        filters.date(
                localtime(json_to_datetime(nodes_timestamps['failed-node']['catalog'])),
                'Y-m-d H:i:s'),
        merged_expected = [('failed-node.example.com',
                            filters.date(localtime(json_to_datetime(nodes_timestamps['failed-node']['catalog'])),
                                         'Y-m-d H:i:s'),
                            filters.date(localtime(json_to_datetime(nodes_timestamps['failed-node']['report'])),
                                         'Y-m-d H:i:s'),
                            filters.date(localtime(json_to_datetime(nodes_timestamps['failed-node']['facts'])),
                                         'Y-m-d H:i:s'),
                            5, 0, 20, 10), (
                               'missmatch-node1.example.com',
                               filters.date(localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['catalog'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['report'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['missmatch-node1']['facts'])),
                                            'Y-m-d H:i:s'),
                               5, 0, 20, 10), (
                               'missmatch-node2.example.com',
                               filters.date(localtime(json_to_datetime(nodes_timestamps['missmatch-node2']['catalog'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['missmatch-node2']['report'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['missmatch-node2']['facts'])),
                                            'Y-m-d H:i:s'),
                               25, 0, 0, 0), (
                               'missmatch-node3.example.com',
                               filters.date(localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['catalog'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['report'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['missmatch-node3']['facts'])),
                                            'Y-m-d H:i:s'),
                               0, 50, 0, 0), (
                               'unreported-node.example.com',
                               filters.date(localtime(json_to_datetime(nodes_timestamps['unreported-node']['catalog'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['unreported-node']['report'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['unreported-node']['facts'])),
                                            'Y-m-d H:i:s'),
                               0, 0, 0, 0), (
                               'changed-node.example.com',
                               filters.date(localtime(json_to_datetime(nodes_timestamps['changed-node']['catalog'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['changed-node']['report'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['changed-node']['facts'])),
                                            'Y-m-d H:i:s'),
                               78, 0, 0, 0), (
                               'unchanged-node.example.com',
                               filters.date(localtime(json_to_datetime(nodes_timestamps['unchanged-node']['catalog'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['unchanged-node']['report'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['unchanged-node']['facts'])),
                                            'Y-m-d H:i:s'),
                               0, 0, 0, 0), (
                               'pending-node.example.com',
                               filters.date(localtime(json_to_datetime(nodes_timestamps['pending-node']['catalog'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['pending-node']['report'])),
                                            'Y-m-d H:i:s'),
                               filters.date(localtime(json_to_datetime(nodes_timestamps['pending-node']['facts'])),
                                            'Y-m-d H:i:s'),
                           0, 100, 0, 0)]
        # failed_list, changed_list, unreported_list, mismatch_list, pending_list
        self.assertEqual(merged_list, merged_expected)
