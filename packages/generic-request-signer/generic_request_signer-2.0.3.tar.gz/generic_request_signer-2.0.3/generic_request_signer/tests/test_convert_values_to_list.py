import unittest
from generic_request_signer.convert_values_to_list import ConvertValuesToList


class ConvertValuesToListTests(unittest.TestCase):

    def test_does_not_wrap_list(self):
        actual_list = ConvertValuesToList()
        with self.assertRaises(ValueError):
            actual_list.update(['list'])

    def test_wraps_basic_dictionary_values(self):
        actual_dict = ConvertValuesToList()
        actual_dict.update({'one': 'zebra', 'two': 'monkey'})
        expected = {'one': ['zebra'], 'two': ['monkey']}
        self.assertEqual(expected, dict(actual_dict))

    def test_converts_integers_to_strings(self):
        actual_dict = ConvertValuesToList()
        actual_dict.update({'one': 1, 'two': 2})
        expected = {'one': ['1'], 'two': ['2']}
        self.assertEqual(expected, dict(actual_dict))

    def test_converts_does_not_wrap_list_values_in_lists(self):
        actual_dict = ConvertValuesToList()
        actual_dict.update({'one': ['leave me alone'], 'two': ['me too']})
        expected = {'one': ['leave me alone'], 'two': ['me too']}
        self.assertEqual(expected, dict(actual_dict))

    def test_converts_nested_values_one_level_deep(self):
        actual_dict = ConvertValuesToList()
        actual_dict.update({'one': {'three': 'another one'}, 'two': ['me too']})
        expected = {'one': [{'three': 'another one'}], 'two': ['me too']}
        self.assertEqual(expected, dict(actual_dict))
