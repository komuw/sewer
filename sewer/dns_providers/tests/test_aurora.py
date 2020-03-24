from unittest import mock
from unittest import TestCase

import sewer

from . import test_utils


class TestAurora(TestCase):
    """
    Test the functionality of Aurora DNS.
    Todo: add proper tests that test that AuroraDns servers are actually called,
    and called with the right parameters. Currently the way the AuroraDns class is,
    makes it hard to mock stuff out.
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.AURORA_API_KEY = "mock-aurora-api-key"
        self.AURORA_SECRET_KEY = "mock-aurora-secret-key"

        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class = sewer.AuroraDns(
                AURORA_API_KEY=self.AURORA_API_KEY, AURORA_SECRET_KEY=self.AURORA_SECRET_KEY
            )

    def tearDown(self):
        pass

    def test_delete_dns_record_is_not_called_by_create_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("requests.delete") as mock_requests_delete, mock.patch(
            "sewer.dns_providers.auroradns.get_driver"
        ) as mock_get_driver, mock.patch(
            "sewer.AuroraDns.delete_dns_record"
        ) as mock_delete_dns_record:
            mock_requests_post.return_value = (
                mock_requests_get.return_value
            ) = (
                mock_requests_delete.return_value
            ) = mock_delete_dns_record.return_value = test_utils.MockResponse()
            mock_get_driver.return_value = test_utils.mockLibcloudGetDriver("mock-provider")

            self.dns_class.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertFalse(mock_delete_dns_record.called)

    def test_aurora_is_called_by_delete_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("requests.delete") as mock_requests_delete, mock.patch(
            "sewer.dns_providers.auroradns.get_driver"
        ) as mock_get_driver:
            mock_requests_post.return_value = (
                mock_requests_get.return_value
            ) = mock_requests_delete.return_value = test_utils.MockResponse()
            mock_get_driver.return_value = test_utils.mockLibcloudGetDriver("mock-provider")

            self.dns_class.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
