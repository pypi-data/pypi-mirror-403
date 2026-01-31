import json
import os
import re
import socket
import time
import itertools
import mimetypes
import six
from random import randint
from collections import OrderedDict

if six.PY2:
    from urllib import urlencode, quote
else:
    from urllib.parse import urlencode, quote

import apysigner

from . import request
from generic_request_signer import constants
from generic_request_signer.convert_values_to_list import ConvertValuesToList


def default_encoding(raw_data, querystring=False):
    encoded_url = urlencode(OrderedDict(sorted(raw_data.items())), doseq=True)
    if six.PY2 or querystring:
        return encoded_url
    return encoded_url.encode()


def json_encoding(raw_data, *args):
    return raw_data


class SignedRequestFactory(object):

    def __init__(self, http_method, client_id, private_key, data, files=None):
        self.client_id = client_id
        self.private_key = private_key
        self.http_method = http_method
        self.raw_data = data
        self.files = files
        self.content_type_encodings = {
            'application/json': json_encoding,
            'application/vnd.api+json': json_encoding,
        }

    @property
    def input_files(self):
        return self.files if isinstance(self.files, list) else [self.files]

    def create_request(self, url, *args, **request_kwargs):
        headers = request_kwargs.get("headers", {})
        url = self.build_request_url(url, headers)
        data = self._get_data_payload(headers)
        return request.Request(self.http_method, url, data, *args, **request_kwargs)

    def build_request_url(self, url, headers):
        url = self._build_client_url(url)
        if self.should_data_be_sent_on_querystring():
            url += "&{0}".format(default_encoding(self.raw_data, querystring=True))
        return self._build_signed_url(url, headers)

    def _build_signed_url(self, url, headers):
        data = {} if self.should_data_be_sent_on_querystring() else self._build_signature_dict_for_content_type(headers)
        signature = apysigner.get_signature(self.private_key, url, data)
        signed_url = self._escape_url(url) + "&{}={}".format(constants.SIGNATURE_PARAM_NAME, signature)
        return signed_url

    def _escape_url(self, url):
        match = re.search(r'(^.+://)([^?]+)(\?.+$)?', url)
        return match.group(1) + quote(match.group(2)) + (match.group(3) if match.group(3) is not None else '')

    def _build_signature_dict_for_content_type(self, headers):  # noqa: C901
        content_type = headers.get("Content-Type")
        if content_type and content_type in ["application/json", "application/vnd.api+json"]:
            encoding_func = self.content_type_encodings.get(content_type, default_encoding)
            return encoding_func(self.raw_data)
        if self.raw_data:
            multi_dict = ConvertValuesToList()
            if isinstance(self.raw_data, str):
                multi_dict.update(json.loads(self.raw_data))
            else:
                multi_dict.update(self.raw_data)
            return dict(multi_dict)
        return {}

    def _get_data_payload(self, request_headers):
        if self.raw_data and not self.method_uses_querystring():
            content_type = request_headers.get("Content-Type")
            encoding_func = self.content_type_encodings.get(content_type, default_encoding)
            encoded_data = encoding_func(self.raw_data)
            if not six.PY2 and isinstance(self.raw_data, str):
                return encoded_data.encode()
            return encoded_data

    def should_data_be_sent_on_querystring(self):
        return self.method_uses_querystring() and self.raw_data

    def method_uses_querystring(self):
        return self.http_method.lower() in ('get', 'delete')

    def _build_client_url(self, url):
        url += "?%s=%s" % (constants.CLIENT_ID_PARAM_NAME, self.client_id)
        return url


class MultipartSignedRequestFactory(SignedRequestFactory):
    FIELD = 'Content-Disposition: form-data; name="{}"'
    FILE = 'Content-Disposition: file; name="{}"; filename="{}"'

    def __init__(self, *args, **kwargs):
        super(MultipartSignedRequestFactory, self).__init__(*args, **kwargs)
        self.boundary_prefix = None
        self.boundary = self.choose_boundary()
        self.part_boundary = "--" + self.boundary

    def create_request(self, url, *args, **request_kwargs):
        headers = request_kwargs.get("headers", {})
        url = self.build_request_url(url, headers)
        body = self.get_multipart_body(self.raw_data)
        return self._build_request(body, url)

    def _build_request(self, body, url):
        new_request = request.Request(self.http_method, url, None)
        new_request.data = body
        new_request.add_header('Content-type', 'multipart/form-data; boundary={}'.format(self.boundary).encode())
        return new_request

    def get_multipart_body(self, data):
        parts = []
        parts.extend(self.get_multipart_fields(data))
        parts.extend(self.get_multipart_files())
        return self.flatten_multipart_body(parts)

    def get_multipart_fields(self, data):
        for name, value in data.items():
            yield [self.part_boundary.encode(), self.FIELD.format(name).encode(), ''.encode(), str(value).encode()]

    def get_multipart_files(self):  # noqa: C901
        for input_file in self.input_files:
            for field_name, (filename, body) in input_file.items():
                read_body = body.read()
                if not isinstance(read_body, six.binary_type):
                    read_body = read_body.encode()
                yield [
                    self.part_boundary.encode(),
                    self.FILE.format(field_name, filename).encode(),
                    self.get_content_type(filename), ''.encode(), read_body
                ]

    def get_content_type(self, filename):
        return 'Content-Type: {}'.format(mimetypes.guess_type(filename)[0] or 'application/octet-stream').encode()

    def flatten_multipart_body(self, parts):
        flattened = list(itertools.chain(*parts))
        boundary_part = self.part_boundary + '--'
        flattened.append(boundary_part.encode())
        flattened.append(''.encode())
        return '\r\n'.encode().join(flattened)

    def choose_boundary(self):  # noqa: C901
        if not self.boundary_prefix:
            try:
                hostid = socket.gethostbyname(socket.gethostname())
            except socket.gaierror:
                hostid = '127.0.0.1'
            try:
                uid = repr(os.getuid())
            except AttributeError:
                uid = '1'
            try:
                pid = repr(os.getpid())
            except AttributeError:
                pid = '1'
            self.boundary_prefix = hostid + '.' + uid + '.' + pid
        return '{}.{}.{}'.format(self.boundary_prefix, time.time(), randint(1000, 10000))
