import mock
from unittest import TestCase

import sewer

class TestPowerDNS(TestCase):
    """
    Tests for PowerDNS DNS provider class.
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.powerdns_api_key = "mock-api-key"
        self.powerdns_api_url = "https://some-mock-url.com"
        self.powerdns_common_response = 204
        self.powerdns_apex_response = 200
        self.dns_class = sewer.PowerDNSDns(
            powerdns_api_key=self.powerdns_api_key, powerdns_api_url=self.powerdns_api_url
        )

    def tearDown(self):
        pass

    def test_validate_powerdns_zone(self):
        fqdn = f"fu.bar.baz.{self.domain_name}"

        with mock.patch("requests.get") as mock_requests_get, mock.patch(
            "sewer.PowerDNSDns.validate_powerdns_zone"
        ) as mock_validate_powerdns_zone:

            mock_requests_get.return_value.status_code = self.powerdns_apex_response
            mock_validate_powerdns_zone.return_value = self.domain_name

            response = self.dns_class.validate_powerdns_zone(fqdn)

        self.assertEqual(response, self.domain_name)
        mock_validate_powerdns_zone.assert_called_with(fqdn)

    def test_powerdns_is_called_by_create_dns_record(self):
        with mock.patch("requests.patch") as mock_requests_patch, mock.patch(
            "sewer.PowerDNSDns.create_dns_record"
        ) as mock_create_dns_record:

            mock_requests_patch.return_value = self.powerdns_common_response

            mock_requests_patch.return_value = (
                mock_create_dns_record.return_value
            ) = self.powerdns_common_response

            self.dns_class.create_dns_record(self.domain_name, self.domain_dns_value)

        self.assertEqual(mock_requests_patch.return_value, self.powerdns_common_response)
        mock_create_dns_record.assert_called_with(self.domain_name, self.domain_dns_value)

    def test_powerdns_is_called_by_delete_dns_record(self):
        with mock.patch("requests.patch") as mock_requests_patch, mock.patch(
            "sewer.PowerDNSDns.delete_dns_record"
        ) as mock_delete_dns_record:
            mock_requests_patch.return_value = self.powerdns_common_response

            mock_requests_patch.return_value = (
                mock_delete_dns_record.return_value
            ) = self.powerdns_common_response

            self.dns_class.delete_dns_record(self.domain_name, self.domain_dns_value)

        self.assertEqual(mock_requests_patch.return_value, self.powerdns_common_response)
        mock_delete_dns_record.assert_called_with(self.domain_name, self.domain_dns_value)
