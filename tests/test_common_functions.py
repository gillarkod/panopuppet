__author__ = 'etaklar'
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
        self.assertEquals(results, expected_result)

    def test_get_percentage_4(self):
        """
        Test is 100/0 should return 0 since division by zero is impossible.
        Result is a string fyi.
        """
        expected_result = '0'
        results = get_percentage(100, 0)
        self.assertEquals(results, expected_result)

    def test_get_percentage_5(self):
        """
        Test is word/100 should fail.
        """
        self.assertRaises(ValueError, get_percentage, value='word', max_val=100)

    def test_get_percentage_6(self):
        """
        Test is word/bird should fail.
        """
        self.assertRaises(ValueError, get_percentage, value='word', max_val='bird')

    def test_get_percentage_7(self):
        """
        Test is 100/bird should fail.
        """
        self.assertRaises(ValueError, get_percentage, value=100, max_val='bird')
