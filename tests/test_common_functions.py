__author__ = 'etaklar'
from datetime import datetime, timedelta
import json
from django.test import TestCase
from pano.templatetags.common import get_percentage


class common_functions(TestCase):
    def test_get_percentage_1(self):
        """
        Test is 50/100 returns correct percentage result
        Result is a string fyi.
        """
        expected_result = '50'
        results = get_percentage(50, 100)
        self.assertEquals(results, expected_result)

    def test_get_percentage_2(self):
        """
        Test is 25/25 returns correct percentage result
        Result is a string fyi.
        """
        expected_result = '100'
        results = get_percentage(25, 25)
        self.assertEquals(results, expected_result)

    def test_get_percentage_3(self):
        """
        Test is 0/0 should return 0 since division by zero is impossible.
        Result is a string fyi.
        """
        expected_result = '0'
        results = get_percentage(0, 0)
        print(results)
        self.assertEquals(results, expected_result)

    def test_get_percentage_4(self):
        """
        Test is 100/0 should return 0 since division by zero is impossible.
        Result is a string fyi.
        """
        expected_result = '0'
        results = get_percentage(100, 0)
        self.assertEquals(results, expected_result)
