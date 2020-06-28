from unittest import mock
from unittest import TestCase

from sewer.dns_providers.dnspod import DNSPodDns

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
        self.test_datas = [
            {
                "domain_name": "example.com",
                "domain_dns_value": "mock-domain_dns_value",
                "expected_domain_name": "example.com",
                "expected_sub_domain_name": "_acme-challenge",
            },
            {
                "domain_name": "sub1.example.com",
                "domain_dns_value": "mock-domain_dns_value",
                "expected_domain_name": "example.com",
                "expected_sub_domain_name": "_acme-challenge.sub1",
            },
            {
                "domain_name": "sub1.sub2.example.com",
                "domain_dns_value": "mock-domain_dns_value",
                "expected_domain_name": "example.com",
                "expected_sub_domain_name": "_acme-challenge.sub1.sub2",
            },
        ]

        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class = DNSPodDns(
                DNSPOD_ID=self.DNSPOD_ID,
                DNSPOD_API_KEY=self.DNSPOD_API_KEY,
                DNSPOD_API_BASE_URL=self.DNSPOD_API_BASE_URL,
            )

    def tearDown(self):
        pass

    def test_delete_dns_record_is_not_called_by_create_dns_record(
        self,
    ):  # actually I don't know the purpose of this.
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "sewer.dns_providers.dnspod.DNSPodDns.delete_dns_record"
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
            "sewer.dns_providers.dnspod.DNSPodDns.delete_dns_record"
        ) as mock_delete_dns_record:
            for test_data in self.test_datas:
                mock_resp = {"status": {"code": "1", "message": "Action completed successful"}}
                mock_requests_post.return_value = (
                    mock_requests_get.return_value
                ) = (
                    mock_requests_delete.return_value
                ) = mock_delete_dns_record.return_value = test_utils.MockResponse(content=mock_resp)

                self.dns_class.create_dns_record(
                    domain_name=test_data["domain_name"],
                    domain_dns_value=test_data["domain_dns_value"],
                )
                expected = {
                    "record_type": "TXT",
                    "domain": test_data["expected_domain_name"],
                    "sub_domain": test_data["expected_sub_domain_name"],
                    "value": test_data["domain_dns_value"],
                    "record_line_id": "0",
                    "format": "json",
                    "login_token": "0123456,mock-api-key",
                }
                self.assertDictEqual(expected, mock_requests_post.call_args[1]["data"])

    def test_dnspod_is_called_by_delete_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("requests.delete") as mock_requests_delete:
            for test_data in self.test_datas:
                mock_resp = {
                    "status": {"code": "1", "message": "Action completed successful"},
                    "records": [
                        {
                            "id": "123456789",
                            "value": "32156546311615",
                            "name": test_data["expected_sub_domain_name"],
                            "type": "TXT",
                        }
                    ],
                }

                mock_requests_post.return_value = (
                    mock_requests_delete.return_value
                ) = test_utils.MockResponse(content=mock_resp)

                mock_requests_get.return_value = test_utils.MockResponse()

                self.dns_class.delete_dns_record(
                    domain_name=test_data["domain_name"],
                    domain_dns_value=test_data["domain_dns_value"],
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
            "sewer.dns_providers.dnspod.DNSPodDns.delete_dns_record"
        ) as mock_delete_dns_record:
            for test_data in self.test_datas:
                mock_resp = {"status": {"code": "-15", "message": "Domain name has been banned."}}
                mock_requests_post.return_value = (
                    mock_requests_get.return_value
                ) = (
                    mock_requests_delete.return_value
                ) = mock_delete_dns_record.return_value = test_utils.MockResponse(content=mock_resp)

                self.assertRaises(
                    ValueError,
                    self.dns_class.create_dns_record,
                    test_data["domain_name"],
                    domain_dns_value=self.domain_dns_value,
                )
