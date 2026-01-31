import six
import json


class Response(object):

    def __init__(self, response):
        self.original_raw_response = None
        self.raw_response = response

    @property
    def status_code(self):
        return self.raw_response.code

    def read(self):
        if self.original_raw_response is None:
            self.original_raw_response = self.raw_response.read()
        return self.original_raw_response

    @property
    def json(self):
        response_content = self.read()
        if response_content == ''.encode():
            return {}
        if six.PY3 and isinstance(response_content, bytes):
            response_content = bytes.decode(response_content, 'utf-8')
        return json.loads(response_content)

    @property
    def is_successful(self):
        return self._evaluate_response_code_for_success(self.status_code)

    def _evaluate_response_code_for_success(self, response_code):
        return response_code // 100 == 2
