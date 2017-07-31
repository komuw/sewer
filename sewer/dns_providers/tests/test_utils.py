import json


class MockResponse(object):
    """
    mock python-requests Response object
    """

    def __init__(self, status_code=200, content='{"something": "ok"}'):
        self.status_code = status_code
        self.content = content
        self.headers = {}

    def json(self):
        return json.loads(self.content)
