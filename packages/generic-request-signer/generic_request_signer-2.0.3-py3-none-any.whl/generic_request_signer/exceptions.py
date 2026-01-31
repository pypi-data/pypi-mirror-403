class WebException(Exception):
    """
    Base Exception for client errors
    """

    def __init__(self, message=''):
        self.message = message
        super(WebException, self).__init__()


class HttpMethodNotAllowed(Exception):
    pass
