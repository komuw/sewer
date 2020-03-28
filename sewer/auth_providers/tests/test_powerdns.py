from unittest import mock
from unittest import TestCase
import sewer

from . import test_utils


class TestPowerDNS(TestCase):
    """
    Tests for PowerDNS DNS provider class.
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.powerdns_api_key = "mock-api-key"
        self.powerdns_api_url = "https://some-mock-url.com"

        self.common_response = test_utils.MockResponse(status_code=204)
        self.apex_response = test_utils.MockResponse(status_code=200)
        with mock.patch("requests.patch") as mock_requests_get:
            mock_requests_get.return_value = self.common_response
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

            mock_requests_get.return_value.status_code = self.apex_response
            mock_validate_powerdns_zone.return_value = self.domain_name

            response = self.dns_class.validate_powerdns_zone(fqdn)

        self.assertEqual(response, self.domain_name)
        mock_validate_powerdns_zone.assert_called_with(fqdn)

    def test_could_not_determine_apex_domain(self):
        with mock.patch("requests.get") as mock_requests_get:
            mock_requests_get.return_value.status_code = 666

            self.assertRaises(
                ValueError, self.dns_class.validate_powerdns_zone, domain_name=self.domain_name
            )

    def test_powerdns_has_correct_changetype(self):
        self.assertRaises(
            ValueError,
            self.dns_class._common_dns_record,
            domain_name=self.domain_name,
            domain_dns_value=self.domain_dns_value,
            changetype="fubar",
        )

    def test_powerdns_returns_correct_status_code(self):
        with mock.patch("requests.patch") as mock_requests_patch, mock.patch(
            "requests.get"
        ) as mock_requests_get:

            mock_requests_get.return_value = self.apex_response
            mock_requests_patch.return_value.status_code = 666

            self.assertRaises(
                ValueError,
                self.dns_class.create_dns_record,
                domain_name=self.domain_name,
                domain_dns_value=self.domain_dns_value,
            )

    def test_powerdns_is_called_by_create_dns_record(self):
        with mock.patch("requests.patch") as mock_requests_patch, mock.patch(
            "sewer.PowerDNSDns.delete_dns_record"
        ) as mock_delete_dns_record, mock.patch("requests.get") as mock_requests_get:

            mock_requests_get.return_value = self.apex_response
            mock_requests_patch.return_value = (
                mock_delete_dns_record.return_value
            ) = self.common_response

            self.dns_class.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )

    def test_powerdns_is_called_by_delete_dns_record(self):
        with mock.patch("requests.patch") as mock_requests_patch, mock.patch(
            "requests.get"
        ) as mock_requests_get:

            mock_requests_get.return_value = self.apex_response
            mock_requests_patch.return_value = self.common_response
            self.dns_class.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertTrue(mock_requests_patch.called)
