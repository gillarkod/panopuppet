__author__ = 'etaklar'

from django.test import TestCase
from pano.puppetdb.puppetdb import mk_puppetdb_query


class CreatePuppetdbQueries(TestCase):
    def test_single_search_query(self):
        content = {
            'query':
                {
                    1: '["=","certname","hostname.example.com"]'
                },
        }
        expected_results = {
            'query': '["=","certname","hostname.example.com"]'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_double_search_query_with_operator(self):
        content = {
            'query':
                {
                    'operator': 'and',
                    1: '["=","hash","e4fug294hf3293hf9348g3804hg3084h"]',
                    2: '["=","latest-report?",true]'
                },
        }
        expected_results = {
            'query': '["and", ["=","hash","e4fug294hf3293hf9348g3804hg3084h"],["=","latest-report?",true]]'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_single_search_query_with_operator(self):
        content = {
            'query':
                {
                    'operator': 'and',
                    1: '["=","hash","e4fug294hf3293hf9348g3804hg3084h"]',
                },
        }
        expected_results = {
            'query': '["and", ["=","hash","e4fug294hf3293hf9348g3804hg3084h"]]'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_summarize_by_query(self):
        content = {
            'summarize-by': 'containing-class',
        }
        expected_results = {
            'summarize-by': 'containing-class'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_summarize_by_query_with_single_search_query(self):
        content = {
            'query':
                {
                    1: '["=","certname","hostname.example.com"]'
                },
            'summarize-by': 'containing-class',
        }
        expected_results = {
            'query': '["=","certname","hostname.example.com"]',
            'summarize-by': 'containing-class'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_order_by_query(self):
        content = {
            'order-by':
                {
                    'order-field':
                        {
                            'field': 'report_timestamp',
                            'order': 'desc',
                        },
                    'query-field':
                        {
                            'field': 'name'
                        },
                }
        }
        expected_results = {
            'order-by': '[{"field":"report_timestamp","order":"desc"},{"field":"name"}]'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_order_by_query_with_single_search_query(self):
        content = {
            'query':
                {
                    1: '["=","certname","hostname.example.com"]'
                },
            'order-by':
                {
                    'order-field':
                        {
                            'field': 'report_timestamp',
                            'order': 'desc',
                        },
                    'query-field':
                        {
                            'field': 'name'
                        },
                }
        }
        expected_results = {
            'order-by': '[{"field":"report_timestamp","order":"desc"},{"field":"name"}]',
            'query': '["=","certname","hostname.example.com"]'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_order_by_query_with_double_search_query_with_operator(self):
        content = {
            'query':
                {
                    'operator': 'or',
                    1: '["=","certname","hostname1.example.com"]',
                    2: '["=","certname","hostname2.example.com"]'
                },
            'order-by':
                {
                    'order-field':
                        {
                            'field': 'report_timestamp',
                            'order': 'desc',
                        },
                    'query-field':
                        {
                            'field': 'name'
                        },
                }
        }
        expected_results = {
            'query': '["and", ["=","certname","hostname1.example.com"],["=","certname","hostname2.example.com"]]',
            'order-by': '[{"field":"report_timestamp","order":"desc"},{"field":"name"}]'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_query_with_string(self):
        content = "string value"
        self.assertRaises(TypeError, mk_puppetdb_query, params=content)
