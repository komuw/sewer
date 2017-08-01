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


class mockLibcloudDriverZone(object):
    """
    A mock of a dns zone in a libcloud drivers dns
    """

    def create_record(self, name, type, data):
        pass


class mockLibcloudDriver(object):
    """
    a mock of libcloud.dns.drivers.auroradns.AuroraDNSDriver class
    """

    def __init__(self, key, secret):
        pass

    def get_zone(self, domainSuffix):
        mock_zone = mockLibcloudDriverZone()
        return mock_zone


def mockLibcloudGetDriver(provider):
    """
    a mock of the libcloud.dns.providers.get_driver function
    """
    return mockLibcloudDriver
