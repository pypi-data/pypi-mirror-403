import six
import unittest

if six.PY3:
    from unittest import mock
else:
    import mock

from generic_request_signer.request import Request
from generic_request_signer.exceptions import HttpMethodNotAllowed


class RequestTests(unittest.TestCase):

    sut_class = Request

    if six.PY3:
        urllib_mock = 'urllib.request.Request.__init__'
    else:
        urllib_mock = 'urllib2.Request.__init__'

    def test_urllib2_super_invoked_with_params(self):
        url = '/'
        data = {}
        args = {'some': 'args'}
        kwargs = {'more': 'kwargs'}
        with mock.patch(self.urllib_mock) as init:
            self.sut_class('GET', url, data, *args, **kwargs)
        init.assert_called_once_with(url, data, *args, **kwargs)

    def test_init_captures_incoming_http_method(self):
        with mock.patch(self.urllib_mock):
            sut = self.sut_class('GET', 'http://', {})
        self.assertEqual(sut.http_method, 'GET')

    def test_get_http_method_returns_correct_method(self):
        sut = self.sut_class('GET', 'http://', {})
        self.assertEqual(sut.get_method(), 'GET')

    def test_will_raise_exception_when_http_method_not_allowed(self):
        with self.assertRaises(HttpMethodNotAllowed):
            self.sut_class('HUH', '/', {})

    def test_will_not_raise_exception_when_http_method_is_allowed(self):
        with self.assertRaises(AssertionError):
            with self.assertRaises(HttpMethodNotAllowed):
                self.sut_class('POST', 'http://', {})

    def test_has_specific_set_of_http_methods_allowed(self):
        allowed_http_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE']
        self.assertEqual(allowed_http_methods, self.sut_class.http_method_names)
