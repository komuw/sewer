import mock
from unittest import TestCase

import sewer

from . import test_utils


class TestDNSPod(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.DNSPOD_ID = "0123456"
        self.DNSPOD_API_KEY = "mock-api-key"
        self.DNSPOD_API_BASE_URL = "https://some-mock-url.com"

        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class = sewer.DNSPodDns(
                DNSPOD_ID=self.DNSPOD_ID,
                DNSPOD_API_KEY=self.DNSPOD_API_KEY,
                DNSPOD_API_BASE_URL=self.DNSPOD_API_BASE_URL,
            )

    def tearDown(self):
        pass

    def test_delete_dns_record_is_not_called_by_create_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "sewer.DNSPodDns.delete_dns_record"
        ) as mock_delete_dns_record:
            mock_resp = {"status": {"code": "1", "message": "Action completed successful"}}
            mock_requests_post.return_value = (
                mock_requests_get.return_value
            ) = mock_delete_dns_record.return_value = test_utils.MockResponse(content=mock_resp)

            self.dns_class.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertFalse(mock_delete_dns_record.called)

    def test_dnspod_is_called_by_create_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("requests.delete") as mock_requests_delete, mock.patch(
            "sewer.DNSPodDns.delete_dns_record"
        ) as mock_delete_dns_record:
            mock_resp = {"status": {"code": "1", "message": "Action completed successful"}}
            mock_requests_post.return_value = (
                mock_requests_get.return_value
            ) = (
                mock_requests_delete.return_value
            ) = mock_delete_dns_record.return_value = test_utils.MockResponse(content=mock_resp)

            self.dns_class.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            expected = {
                "record_type": "TXT",
                "domain": self.domain_name,
                "sub_domain": "_acme-challenge",
                "value": self.domain_dns_value,
                "record_line_id": "0",
                "format": "json",
                "login_token": "0123456,mock-api-key",
            }
            self.assertDictEqual(expected, mock_requests_post.call_args[1]["data"])

    def test_dnspod_is_called_by_delete_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("requests.delete") as mock_requests_delete:
            mock_resp = {
                "status": {"code": "1", "message": "Action completed successful"},
                "records": [
                    {
                        "id": "123456789",
                        "value": "32156546311615",
                        "name": "_acme-challenge",
                        "type": "TXT",
                    }
                ],
            }

            mock_requests_post.return_value = (
                mock_requests_delete.return_value
            ) = test_utils.MockResponse(content=mock_resp)

            mock_requests_get.return_value = test_utils.MockResponse()

            self.dns_class.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertTrue(mock_requests_post.called)
            self.assertIn("123456789", str(mock_requests_post.call_args))
            self.assertIn(
                "https://some-mock-url.com/Record.Remove", str(mock_requests_post.call_args)
            )

    def test_exception_is_raised_if_unsuccessful(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("requests.delete") as mock_requests_delete, mock.patch(
            "sewer.DNSPodDns.delete_dns_record"
        ) as mock_delete_dns_record:
            mock_resp = {"status": {"code": "-15", "message": "Domain name has been banned."}}
            mock_requests_post.return_value = (
                mock_requests_get.return_value
            ) = (
                mock_requests_delete.return_value
            ) = mock_delete_dns_record.return_value = test_utils.MockResponse(content=mock_resp)

            self.assertRaises(
                ValueError,
                self.dns_class.create_dns_record,
                self.domain_name,
                domain_dns_value=self.domain_dns_value,
            )
