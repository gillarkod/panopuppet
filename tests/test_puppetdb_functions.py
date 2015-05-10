__author__ = 'etaklar'

from django.test import TestCase
from pano.puppetdb.puppetdb import mk_puppetdb_query


class CreatePuppetdbQueries(TestCase):
    def test_single_query(self):
        content = {
            'query':
                {
                    1: '["=","certname","hostname.example.com"]'
                },
        }
        expected_results = {'query': '["=","certname","hostname.example.com"]'}
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_double_query_with_operator(self):
        content = {
            'query':
                {
                    'operator': 'and',
                    1: '["=","hash","e4fug294hf3293hf9348g3804hg3084h"]',
                    2: '["=","latest-report?",true]'
                },
        }
        expected_results = {
        'query': '["and", ["=","hash","e4fug294hf3293hf9348g3804hg3084h"],["=","latest-report?",true]]'}
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_single_query_with_operator(self):
        content = {
            'query':
                {
                    'operator': 'and',
                    1: '["=","hash","e4fug294hf3293hf9348g3804hg3084h"]',
                },
        }
        expected_results = {'query': '["and", ["=","hash","e4fug294hf3293hf9348g3804hg3084h"]]'}
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)



