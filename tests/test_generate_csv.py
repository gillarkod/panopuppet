from unittest import TestCase
from pano.puppetdb.pdbutils import generate_csv

__author__ = 'etaklar'


class TestGenerateCsv(TestCase):
    def test_nodes_with_one_fact(self):
        nodes = [
            ('node1.example.com',
             '2015-05-31 20:18:29',
             '2015-05-31 20:20:29',
             '2015-05-31 20:19:29',
             5,
             0,
             20,
             10
             ),
            (
                'node2.example.com',
                '2015-05-31 20:18:29',
                '2015-05-31 20:20:29',
                '2015-05-31 19:34:29',
                5,
                0,
                20,
                10
            ),
            (
                'node3.example.com',
                '2015-05-31 20:18:29',
                '2015-05-31 19:34:29',
                '2015-05-31 20:19:29',
                25,
                0,
                0,
                0
            ),
        ]
        facts_hash = dict()
        include_facts = "kernelversion"

        facts_list = [
            {'certname': 'node1.example.com', 'environment': 'production', 'value': '3.13.0',
             'name': 'kernelversion'},
            {'certname': 'node2.example.com', 'environment': 'production', 'value': '3.13.0',
             'name': 'kernelversion'},
            {'certname': 'node3.example.com', 'environment': 'production', 'value': '3.13.0',
             'name': 'kernelversion'}]
        for fact in include_facts.split(','):
            facts_hash[fact] = {item['certname']: item for item in facts_list}

        i = 1
        jobs = {}
        # Add ID to each job so that it can be assembled in
        # the same order after we recieve the job results
        # We do this via jobs so that we can get faster results.
        for node in nodes:
            jobs[i] = {
                'id': i,
                'include_facts': include_facts.split(','),
                'node': node,
                'facts': facts_hash,
            }
            i += 1
        rows = list()
        csv_results = generate_csv(jobs)
        i = 1
        while i <= len(csv_results):
            rows.append(csv_results[i])
            i += 1

        expected_results = [
            (
                'node1.example.com',
                '2015-05-31 20:18:29',
                '2015-05-31 20:20:29',
                '2015-05-31 20:19:29',
                5,
                0,
                20,
                10,
                '3.13.0'
            ),
            (
                'node2.example.com',
                '2015-05-31 20:18:29',
                '2015-05-31 20:20:29',
                '2015-05-31 19:34:29',
                5,
                0,
                20,
                10,
                '3.13.0'
            ),
            (
                'node3.example.com',
                '2015-05-31 20:18:29',
                '2015-05-31 19:34:29',
                '2015-05-31 20:19:29',
                25,
                0,
                0,
                0,
                '3.13.0'
            ),
        ]
        self.assertEqual(expected_results, rows)
