import json


class MockResponse(object):
    """
    mock python-requests Response object
    """

    def __init__(self, status_code=200, content=None):
        if not content:
            content = {}

        content.update(
            {"something": "ok", "result": [{"name": "example.com", "id": "some-mock-dns-zone-id"}]}
        )
        self.content = json.dumps(content).encode()
        self.status_code = status_code
        self.headers = {}

    def json(self):
        return json.loads(self.content.decode())


class mockLibcloudDriverZone(object):
    """
    A mock of a dns zone in a libcloud drivers dns
    """

    id = "mock-zone-id-1"

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

    def list_records(self, zone):
        import collections

        DnsRecords = collections.namedtuple("DnsRecords", "id name type")
        one_dns_record = DnsRecords(id="1", name="_acme-challenge", type="TXT")
        records = [one_dns_record]
        return records

    def get_record(self, zone_id, record_id):
        return "mock-record"

    def delete_record(self, record):
        pass


def mockLibcloudGetDriver(provider):
    """
    a mock of the libcloud.dns.providers.get_driver function
    """
    return mockLibcloudDriver


class MockDnsResolver(object):
    canonical_name = "canonical.name"
