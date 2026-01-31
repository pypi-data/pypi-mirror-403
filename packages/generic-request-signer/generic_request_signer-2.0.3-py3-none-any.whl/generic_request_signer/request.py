import six

if six.PY3:
    from urllib.request import Request
else:
    from urllib2 import Request

from generic_request_signer.exceptions import HttpMethodNotAllowed


class Request(Request, object):

    http_method_names = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE']

    def __init__(self, http_method, url, data, *args, **kwargs):
        method_upper = http_method.upper()
        if method_upper not in self.http_method_names:
            raise HttpMethodNotAllowed
        self.http_method = method_upper
        super(Request, self).__init__(url, data, *args, **kwargs)

    def get_method(self):
        return self.http_method
