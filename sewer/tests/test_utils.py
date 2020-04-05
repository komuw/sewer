import json

import sewer


class ExmpleDnsProvider(sewer.dns_providers.common.BaseDns):
    def __init__(self):
        self.dns_provider_name = "example_dns_provider"
        super(ExmpleDnsProvider, self).__init__()

    def create_dns_record(self, domain_name, domain_dns_value):
        pass

    def delete_dns_record(self, domain_name, domain_dns_value):
        pass


### FIX ME ### this is now obsolete (see dummy HTTP class below!)


class ExmpleAuthProvider(sewer.auth.BaseAuth):
    def __init__(self):
        super(ExmpleAuthProvider, self).__init__(chal_types=["http-01"])

    def setup_auth(self, domain, token, key_auth):
        return {}

    def clear_auth(self, domain, token, key_auth):
        pass


class ExmpleHttpProvider(sewer.auth.BaseAuth):
    def __init__(self):
        super(ExmpleHttpProvider, self).__init__(chal_types=["http-01"])

    def setup_auth(self, domain, token, key_auth):
        pass

    def clear_auth(self, domain, token, key_auth):
        pass


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
