import mock
import json
from unittest import TestCase

import sewer

from . import test_utils

# TO BE TESTED
class TestDuckDNS(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.duckdns_API_KEY = "mock-api-key"
        self.duckdns_API_BASE_URL = "https://some-mock-url.com"

        with mock.patch("requests.get") as mock_requests_get:
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class = sewer.DuckDNSDns(
                duckdns_token=self.duckdns_API_KEY, DUCKDNS_API_BASE_URL=self.duckdns_API_BASE_URL
            )

    def tearDown(self):
        pass

    def test_duckdns_is_called_by_create_dns_record(self):
        with mock.patch("requests.get") as mock_requests_get, mock.patch(
            "sewer.DuckDNSDns.delete_dns_record"
        ) as mock_delete_dns_record:
            mock_requests_get.return_value = (
                mock_delete_dns_record.return_value
            ) = test_utils.MockResponse()
            self.dns_class.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )

            expected = {
                "data": '{"domains": "example.com", "token": "mock-api-key", "txt": "mock-domain_dns_value"}'
            }

            self.assertDictEqual(
                json.loads(expected["data"]), mock_requests_get.call_args[1]["params"]
            )

    def test_duckdns_is_not_called_by_delete_dns_record(self):
        with mock.patch("requests.get") as mock_requests_get:
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertFalse(mock_requests_get.called)

    def test_duckdns_is_called_by_delete_dns_record(self):
        with mock.patch("requests.get") as mock_requests_get, mock.patch(
            "requests.delete"
        ) as mock_requests_delete:
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertTrue(mock_requests_get.called)
