from unittest import mock
from unittest import TestCase

from sewer.dns_providers.rackspace import RackspaceDns

from . import test_utils


class TestRackspace(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.RACKSPACE_USERNAME = "mock_username"
        self.RACKSPACE_API_KEY = "mock-api-key"
        self.RACKSPACE_API_TOKEN = "mock-api-token"

        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.get_rackspace_credentials"
        ) as mock_get_credentials, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.find_dns_zone_id", autospec=True
        ) as mock_find_dns_zone_id:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            mock_get_credentials.return_value = "mock-api-token", "http://example.com/"
            mock_find_dns_zone_id.return_value = "mock_zone_id"
            self.dns_class = RackspaceDns(
                RACKSPACE_USERNAME=self.RACKSPACE_USERNAME, RACKSPACE_API_KEY=self.RACKSPACE_API_KEY
            )

    def tearDown(self):
        pass

    def test_find_dns_zone_id(self):
        with mock.patch("requests.get") as mock_requests_get:
            # see: https://developer.rackspace.com/docs/cloud-dns/v1/api-reference/domains/
            mock_dns_zone_id = 1_239_932
            mock_requests_content = {
                "domains": [
                    {
                        "name": self.domain_name,
                        "id": mock_dns_zone_id,
                        "comment": "Optional domain comment...",
                        "updated": "2011-06-24T01:23:15.000+0000",
                        "accountId": 1234,
                        "emailAddress": "sample@rackspace.com",
                        "created": "2011-06-24T01:12:51.000+0000",
                    }
                ]
            }
            mock_requests_get.return_value = test_utils.MockResponse(200, mock_requests_content)
            dns_zone_id = self.dns_class.find_dns_zone_id(self.domain_name)
            self.assertEqual(dns_zone_id, mock_dns_zone_id)
            self.assertTrue(mock_requests_get.called)

    def test_find_dns_record_id(self):
        with mock.patch("requests.get") as mock_requests_get, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.find_dns_zone_id"
        ) as mock_find_dns_zone_id:
            # see: https://developer.rackspace.com/docs/cloud-dns/v1/api-reference/records/
            mock_dns_record_id = "A-1234"
            mock_requests_content = {
                "totalEntries": 1,
                "records": [
                    {
                        "name": self.domain_name,
                        "id": mock_dns_record_id,
                        "type": "A",
                        "data": self.domain_dns_value,
                        "updated": "2011-05-19T13:07:08.000+0000",
                        "ttl": 5771,
                        "created": "2011-05-18T19:53:09.000+0000",
                    }
                ],
            }
            mock_requests_get.return_value = test_utils.MockResponse(200, mock_requests_content)
            mock_find_dns_zone_id.return_value = 1_239_932

            dns_record_id = self.dns_class.find_dns_record_id(
                self.domain_name, self.domain_dns_value
            )
            self.assertEqual(dns_record_id, mock_dns_record_id)
            self.assertTrue(mock_requests_get.called)
            self.assertTrue(mock_find_dns_zone_id.called)

    def test_delete_dns_record_is_not_called_by_create_dns_record(self):
        with mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.find_dns_zone_id"
        ) as mock_find_dns_zone_id, mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch(
            "requests.delete"
        ) as mock_requests_delete, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.delete_dns_record"
        ) as mock_delete_dns_record, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.poll_callback_url"
        ) as mock_poll_callback_url:
            mock_find_dns_zone_id.return_value = "mock_zone_id"
            mock_requests_get.return_value = (
                mock_requests_delete.return_value
            ) = mock_delete_dns_record.return_value = test_utils.MockResponse()
            mock_requests_content = {"callbackUrl": "http://example.com/callbackUrl"}
            mock_requests_post.return_value = test_utils.MockResponse(202, mock_requests_content)
            mock_poll_callback_url.return_value = 1
            self.dns_class.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertFalse(mock_delete_dns_record.called)

    def test_rackspace_is_called_by_create_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("requests.delete") as mock_requests_delete, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.delete_dns_record"
        ) as mock_delete_dns_record, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.find_dns_zone_id"
        ) as mock_find_dns_zone_id, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.poll_callback_url"
        ) as mock_poll_callback_url:
            mock_requests_content = {"callbackUrl": "http://example.com/callbackUrl"}
            mock_requests_post.return_value = test_utils.MockResponse(202, mock_requests_content)
            mock_requests_get.return_value = (
                mock_requests_delete.return_value
            ) = mock_delete_dns_record.return_value = test_utils.MockResponse()
            mock_find_dns_zone_id.return_value = "mock_zone_id"
            mock_poll_callback_url.return_value = 1

            self.dns_class.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            expected = {
                "headers": {"X-Auth-Token": "mock-api-token", "Content-Type": "application/json"},
                "data": self.domain_dns_value,
            }
            self.assertDictEqual(expected["headers"], mock_requests_post.call_args[1]["headers"])
            self.assertEqual(
                expected["data"], mock_requests_post.call_args[1]["json"]["records"][0]["data"]
            )

    def test_rackspace_is_called_by_delete_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get, mock.patch("requests.delete") as mock_requests_delete, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.find_dns_zone_id"
        ) as mock_find_dns_zone_id, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.poll_callback_url"
        ) as mock_poll_callback_url, mock.patch(
            "sewer.dns_providers.rackspace.RackspaceDns.find_dns_record_id"
        ) as mock_find_dns_record_id:
            mock_requests_content = {"callbackUrl": "http://example.com/callbackUrl"}
            mock_requests_post.return_value = (
                mock_requests_get.return_value
            ) = test_utils.MockResponse()
            mock_requests_delete.return_value = test_utils.MockResponse(202, mock_requests_content)
            mock_find_dns_zone_id.return_value = "mock_zone_id"
            mock_poll_callback_url.return_value = 1
            mock_find_dns_record_id.return_value = "mock_record_id"

            self.dns_class.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            expected = {
                "headers": {"X-Auth-Token": "mock-api-token", "Content-Type": "application/json"},
                "url": "http://example.com/domains/mock_zone_id/records/?id=mock_record_id",
            }
            self.assertDictEqual(expected["headers"], mock_requests_delete.call_args[1]["headers"])
            self.assertEqual(expected["url"], mock_requests_delete.call_args[0][0])
