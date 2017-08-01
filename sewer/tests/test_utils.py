import json

import sewer


class ExmpleDnsProvider(sewer.dns_providers.common.BaseDns):

    def __init__(self):
        self.dns_provider_name = 'example_dns_provider'

    def create_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        pass

    def delete_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        pass


class MockResponse(object):
    """
    mock python-requests Response object
    """

    def __init__(self, status_code=201, content='{"something": "ok"}'):
        self.status_code = status_code
        self.content = content + '-----BEGIN CERTIFICATE----- some-mock-certificate -----END CERTIFICATE-----'
        self.content_to_use_in_json_method = content
        self.headers = {'Replay-Nonce': 'example-replay-Nonce'}

    def json(self):
        return json.loads(self.content_to_use_in_json_method)
