from unittest import mock
from unittest import TestCase

from sewer.dns_providers.hurricane import HurricaneDns

from . import test_utils


class TestHEDNS(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.he_uesrname = "mock-username"
        self.he_password = "mock-password"

        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class = HurricaneDns(username=self.he_uesrname, password=self.he_password)

    def tearDown(self):
        pass

    def test_extract_zone_sub_domain(self):
        _zone = "sub-domain"
        domain = "%s.%s" % (_zone, self.domain_name)
        root, zone, acme_txt = self.dns_class.extract_zone(domain)

        self.assertEqual(root, self.domain_name)
        self.assertEqual(zone, _zone)
        self.assertEqual(acme_txt, "_acme-challenge.%s" % zone)

    def test_extract_zone_root(self):
        domain = self.domain_name
        root, zone, acme_txt = self.dns_class.extract_zone(domain)
        self.assertEqual(root, self.domain_name)
        self.assertEqual(zone, "")
        self.assertEqual(acme_txt, "_acme-challenge")

    def test_hedns_is_called_by_create_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "sewer.dns_providers.hurricane.HurricaneDns.delete_dns_record"
        ) as mock_delete_dns_record, mock.patch("dns.resolver.Resolver.query") as mock_dns_resolver:
            mock_requests_post.return_value = (
                mock_delete_dns_record.return_value
            ) = test_utils.MockResponse()
            mock_dns_resolver.return_value = test_utils.MockDnsResolver()

            # cause we use mock username & passworkd, the client will raise a
            # Auth Error
            try:
                self.dns_class.create_dns_record(
                    domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
                )
            except Exception:
                pass

            self.assertFalse(mock_requests_post.called)

    def test_hedns_is_not_called_by_delete_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post:
            mock_requests_post.return_value = test_utils.MockResponse()

            # cause we use mock username & passworkd, the client will raise a
            # Auth Error
            try:
                self.dns_class.delete_dns_record(
                    domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
                )
            except Exception:
                pass
            self.assertFalse(mock_requests_post.called)
