import json

from ..auth import ProviderBase
from ..dns_providers.common import BaseDns


class ExmpleDnsProvider(BaseDns):
    def __init__(self, **kwargs):
        self.dns_provider_name = "example_dns_provider"
        super().__init__(**kwargs)

    def create_dns_record(self, domain_name, domain_dns_value):
        pass

    def delete_dns_record(self, domain_name, domain_dns_value):
        pass


class ExmpleDNS(ExmpleDnsProvider):
    "fail unpropagated first n times DNS mock provider"

    def __init__(self, fail_prop_count, **kwargs):
        super().__init__(**kwargs)
        self.fail_prop_count = fail_prop_count

    def unpropagated(self, challenges):
        if self.fail_prop_count <= 0:
            return []
        self.fail_prop_count -= 1
        return [("unready", "", c) for c in challenges]


class ExmpleHttpProvider(ProviderBase):
    def __init__(self):
        super().__init__(chal_types=["http-01"])

    def setup(self, challenges):
        return []

    def unpropagated(self, challenges):
        return []

    def clear(self, challenges):
        return []


class MockResponse(object):
    """
    mock python-requests Response object
    """

    def __init__(self, status_code=201, content=None):
        if not content:
            content = {}
        self.status_code = status_code
        content.update(
            {
                "newNonce": "http://localhost/newNonce",
                "keyChange": "http://localhost/keyChange",
                "newAccount": "http://localhost/newAccount",
                "newOrder": "http://localhost/newOrder",
                "revokeCert": "http://localhost/revokeCert",
                "challenges": [
                    {
                        "type": "dns-01",
                        "token": "example-token",
                        "url": "http://localhost/challenge-url",
                    },
                    {
                        "type": "http-01",
                        "token": "example-token",
                        "url": "http://localhost/challenge-url",
                    },
                ],
                "authorizations": ["http://localhost/authorization-url"],
                "finalize": "http://localhost/finalize-url",
                "status": "valid",
                "certificate": "http://localhost/certificate-url",
                "meta": {"termsOfService": "http:localhost/termsOfService"},
                "dummy-certificate": "-----BEGIN CERTIFICATE----- some-mock-certificate -----END CERTIFICATE-----",
                "identifier": {"value": "example.com"},
                "wildcard": None,
            }
        )

        self.content = json.dumps(content).encode()
        self.content_to_use_in_json_method = self.content
        self.headers = {
            "Replay-Nonce": "example-replay-Nonce",
            "Location": "https://localhost/acme/acct/1",
        }

    def json(self):
        json_d = json.loads(self.content_to_use_in_json_method.decode())
        return json_d
