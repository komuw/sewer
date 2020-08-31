import os, sys
from unittest import mock, skipIf, TestCase

from sewer.dns_providers.cloudns import ClouDNSDns

from . import test_utils


class TestClouDNS(TestCase):
    """
    Tests the ClouDNS DNS provider class.
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.cloudns_auth_id = "mock-api-id"
        self.cloudns_auth_password = "mock-api-password"

        self.dns_class = ClouDNSDns()

        os.environ["CLOUDNS_API_AUTH_ID"] = self.cloudns_auth_id
        os.environ["CLOUDNS_API_AUTH_PASSWORD"] = self.cloudns_auth_password

    def test_cloudns_is_called_by_create_dns_record(self):
        with mock.patch(
            "cloudns_api.api.CLOUDNS_API_AUTH_ID", new=self.cloudns_auth_id
        ), mock.patch(
            "cloudns_api.api.CLOUDNS_API_AUTH_PASSWORD", new=self.cloudns_auth_password
        ), mock.patch(
            "requests.post"
        ) as mock_requests_post:
            mock_requests_post.return_value = test_utils.MockResponse()

            self.dns_class.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )

            expected = {
                "auth-id": "mock-api-id",
                "auth-password": "mock-api-password",
                "domain-name": "example.com",
                "host": "_acme-challenge",
                "record": "mock-domain_dns_value",
                "record-type": "TXT",
                "ttl": 60,
            }

            self.assertDictEqual(expected, mock_requests_post.call_args[1]["params"])

    @skipIf(sys.version_info[:2] == (3, 5), "mysterious failure with Py3.5 only")
    def test_cloudns_is_called_by_delete_dns_record(self):
        with mock.patch(
            "cloudns_api.api.CLOUDNS_API_AUTH_ID", new=self.cloudns_auth_id
        ), mock.patch(
            "cloudns_api.api.CLOUDNS_API_AUTH_PASSWORD", new=self.cloudns_auth_password
        ), mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "requests.post"
        ) as mock_requests_post:

            mock_requests_get.return_value = test_utils.MockResponse(
                content={"1234567": {"record": "mock-domain_dns_value"}}
            )
            mock_requests_post.return_value = test_utils.MockResponse()

            self.dns_class.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )

            expected = {
                "auth-id": "mock-api-id",
                "auth-password": "mock-api-password",
                "domain-name": "example.com",
                "record-id": "1234567",
            }

            self.assertDictEqual(expected, mock_requests_post.call_args[1]["params"])
