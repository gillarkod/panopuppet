from django.test import TestCase

from pano.puppetdb.puppetdb import mk_puppetdb_query

__author__ = 'etaklar'


class CreatePuppetdbQueries(TestCase):
    def test_single_search_query(self):
        content = {
            'query':
                {
                    1: '["=","certname","hostname.example.com"]'
                },
        }
        expected_results = {
            'query': '["and",["=","certname","hostname.example.com"]]'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_double_search_query_with_operator(self):
        content = {
            'query':
                {
                    'operator': 'and',
                    1: '["=","hash","e4fug294hf3293hf9348g3804hg3084h"]',
                    2: '["=","latest_report?",true]'
                },
        }
        expected_results = {
            'query': '["and",["=","hash","e4fug294hf3293hf9348g3804hg3084h"],["=","latest_report?",true]]'
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
            'query': '["and",["=","hash","e4fug294hf3293hf9348g3804hg3084h"]]'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_summarize_by_query(self):
        content = {
            'summarize_by': 'containing_class',
        }
        expected_results = {
            'summarize_by': 'containing_class'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_summarize_by_query_with_single_search_query(self):
        content = {
            'query':
                {
                    1: '["=","certname","hostname.example.com"]'
                },
            'summarize_by': 'containing_class',
        }
        expected_results = {
            'query': '["and",["=","certname","hostname.example.com"]]',
            'summarize_by': 'containing_class'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_order_by_query(self):
        content = {
            'order_by':
                {
                    'order_field':
                        {
                            'field': 'report_timestamp',
                            'order': 'desc',
                        },
                }
        }
        expected_results = {
            'order_by': '[{"field":"report_timestamp","order":"desc"}]'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_order_by_query_with_single_search_query(self):
        content = {
            'query':
                {
                    1: '["=","certname","hostname.example.com"]'
                },
            'order_by':
                {
                    'order_field':
                        {
                            'field': 'report_timestamp',
                            'order': 'desc',
                        },
                }
        }
        expected_results = {
            'order_by': '[{"field":"report_timestamp","order":"desc"}]',
            'query': '["and",["=","certname","hostname.example.com"]]'
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
            'order_by':
                {
                    'order_field':
                        {
                            'field': 'report_timestamp',
                            'order': 'desc',
                        },
                }
        }
        expected_results = {
            'query': '["and",["=","certname","hostname1.example.com"],["=","certname","hostname2.example.com"]]',
            'order_by': '[{"field":"report_timestamp","order":"desc"}]'
        }
        results = mk_puppetdb_query(content)
        self.assertEqual(expected_results, results)

    def test_query_with_string(self):
        content = "string value"
        self.assertRaises(TypeError, mk_puppetdb_query, params=content)

    def test_query_with_list(self):
        content = ['test1', 'test2']
        self.assertRaises(TypeError, mk_puppetdb_query, params=content)

    def test_query_with_integer(self):
        content = 1
        self.assertRaises(TypeError, mk_puppetdb_query, params=content)

    def test_query_with_empty_dict(self):
        content = {}
        expected_results = {}
        self.assertEquals(content, expected_results)
