from unittest import mock
import json
from unittest import TestCase

import sewer

from . import test_utils


class TestCloudflare(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.CLOUDFLARE_EMAIL = "mock-email@example.com"
        self.CLOUDFLARE_API_KEY = "mock-api-key"
        self.CLOUDFLARE_API_BASE_URL = "https://some-mock-url.com"
        self.CLOUDFLARE_TOKEN = "mock-token"

        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class_api_key = sewer.create_auth_provider("CloudFlareDns",
                CLOUDFLARE_EMAIL=self.CLOUDFLARE_EMAIL,
                CLOUDFLARE_API_KEY=self.CLOUDFLARE_API_KEY,
                CLOUDFLARE_API_BASE_URL=self.CLOUDFLARE_API_BASE_URL,
            )

        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class_token = sewer.create_auth_provider("CloudFlareDns",
                CLOUDFLARE_TOKEN=self.CLOUDFLARE_TOKEN,
                CLOUDFLARE_API_BASE_URL=self.CLOUDFLARE_API_BASE_URL,
            )

    def tearDown(self):
        pass

    def test_delete_dns_record_is_not_called_by_create_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, \
        mock.patch("requests.get") as mock_requests_get, \
        mock.patch("requests.delete") as mock_requests_delete, \
        mock.patch("sewer.auth_providers.cloudflare.CloudFlareDns.delete_dns_record") as mock_delete_dns_record:
            mock_requests_post.return_value = (
                mock_requests_get.return_value
            ) = (
                mock_requests_delete.return_value
            ) = mock_delete_dns_record.return_value = test_utils.MockResponse()

            self.dns_class_api_key.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertFalse(mock_delete_dns_record.called)

            self.dns_class_token.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertFalse(mock_delete_dns_record.called)

    def test_cloudflare_is_called_by_create_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("requests.delete") as mock_requests_delete, mock.patch(
            "sewer.auth_providers.cloudflare.CloudFlareDns.delete_dns_record"
        ) as mock_delete_dns_record:
            mock_requests_post.return_value = (
                mock_requests_get.return_value
            ) = (
                mock_requests_delete.return_value
            ) = mock_delete_dns_record.return_value = test_utils.MockResponse()

            # Test with API key authentication
            self.dns_class_api_key.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            expected = {
                "headers": {
                    "X-Auth-Email": self.CLOUDFLARE_EMAIL,
                    "X-Auth-Key": self.CLOUDFLARE_API_KEY,
                },
                "data": '{"content": "mock-domain_dns_value", "type": "TXT", "name": "_acme-challenge.example.com."}',
                "timeout": 65,
            }

            self.assertDictEqual(expected["headers"], mock_requests_post.call_args[1]["headers"])
            self.assertDictEqual(
                json.loads(expected["data"]), mock_requests_post.call_args[1]["json"]
            )

            # Test with token authentication
            self.dns_class_token.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            expected = {
                "headers": {"Authorization": "Bearer " + self.CLOUDFLARE_TOKEN},
                "data": '{"content": "mock-domain_dns_value", "type": "TXT", "name": "_acme-challenge.example.com."}',
                "timeout": 65,
            }

            self.assertDictEqual(expected["headers"], mock_requests_post.call_args[1]["headers"])
            self.assertDictEqual(
                json.loads(expected["data"]), mock_requests_post.call_args[1]["json"]
            )

    def test_cloudflare_is_called_by_delete_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("requests.delete") as mock_requests_delete:
            mock_requests_post.return_value = (
                mock_requests_delete.return_value
            ) = test_utils.MockResponse()

            mock_requests_get.return_value = test_utils.MockResponse()

            # Test with API key authentication
            self.dns_class_api_key.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertTrue(mock_requests_get.called)
            expected = {
                "headers": {
                    "X-Auth-Email": self.CLOUDFLARE_EMAIL,
                    "X-Auth-Key": self.CLOUDFLARE_API_KEY,
                },
                "timeout": 65,
            }
            self.assertDictEqual(expected, mock_requests_delete.call_args[1])
            self.assertIn(
                "https://some-mock-url.com/zones/None/dns_records/some-mock-dns-zone-id",
                str(mock_requests_delete.call_args),
            )

            # Test with token authentication
            self.dns_class_token.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertTrue(mock_requests_get.called)
            expected = {
                "headers": {"Authorization": "Bearer " + self.CLOUDFLARE_TOKEN},
                "timeout": 65,
            }
            self.assertDictEqual(expected, mock_requests_delete.call_args[1])
            self.assertIn(
                "https://some-mock-url.com/zones/None/dns_records/some-mock-dns-zone-id",
                str(mock_requests_delete.call_args),
            )


class TestCloudflareTokens(TestCase):
    """
    Test that the authorization parameters are validated (either email + API key or token)
    """

    def setUp(self):
        self.CLOUDFLARE_EMAIL = "mock-email@example.com"
        self.CLOUDFLARE_API_KEY = "mock-api-key"
        self.CLOUDFLARE_TOKEN = "some-token"

    def test_init_auth_validation(self):
        # Invalid inputs
        with self.assertRaises(ValueError):
            sewer.create_auth_provider("CloudFlareDns",
                CLOUDFLARE_TOKEN=self.CLOUDFLARE_TOKEN,
                CLOUDFLARE_EMAIL=self.CLOUDFLARE_EMAIL,
                CLOUDFLARE_API_KEY=self.CLOUDFLARE_API_KEY,
            )

        with self.assertRaises(ValueError):
            sewer.create_auth_provider("CloudFlareDns",
                CLOUDFLARE_TOKEN=self.CLOUDFLARE_TOKEN, CLOUDFLARE_API_KEY=self.CLOUDFLARE_API_KEY
            )

        with self.assertRaises(ValueError):
            sewer.create_auth_provider("CloudFlareDns",)

        with self.assertRaises(ValueError):
            sewer.create_auth_provider("CloudFlareDns",
                CLOUDFLARE_TOKEN=self.CLOUDFLARE_TOKEN, CLOUDFLARE_EMAIL=self.CLOUDFLARE_EMAIL
            )

        # Valid inputs
        sewer.create_auth_provider("CloudFlareDns",
            CLOUDFLARE_EMAIL=self.CLOUDFLARE_EMAIL, CLOUDFLARE_API_KEY=self.CLOUDFLARE_API_KEY
        )
        sewer.create_auth_provider("CloudFlareDns",CLOUDFLARE_TOKEN=self.CLOUDFLARE_TOKEN)
