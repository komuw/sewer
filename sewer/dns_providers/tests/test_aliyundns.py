from unittest import mock
from unittest import TestCase
import sewer
from . import test_utils


class TestAliyunDNS(TestCase):
    """
    """

    def setUp(self):
        self.domain_name = "example.com"
        self.domain_dns_value = "mock-domain_dns_value"
        self.API_KEY = "mock-api-key"
        self.API_SECRET = "mock-api-secret"

        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "requests.get"
        ) as mock_requests_get:
            mock_requests_post.return_value = test_utils.MockResponse()
            mock_requests_get.return_value = test_utils.MockResponse()
            self.dns_class = sewer.AliyunDns(key=self.API_KEY, secret=self.API_SECRET)

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

    def test_aliyun_is_called_by_create_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post, mock.patch(
            "sewer.AliyunDns.delete_dns_record"
        ) as mock_delete_dns_record, mock.patch("dns.resolver.Resolver.query") as mock_dns_resolver:
            mock_requests_post.return_value = (
                mock_delete_dns_record.return_value
            ) = test_utils.MockResponse()
            mock_dns_resolver.return_value = test_utils.MockDnsResolver()
            self.dns_class.create_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )

            self.assertFalse(mock_requests_post.called)

    def test_aliyun_is_not_called_by_delete_dns_record(self):
        with mock.patch("requests.post") as mock_requests_post:
            mock_requests_post.return_value = test_utils.MockResponse()
            self.dns_class.delete_dns_record(
                domain_name=self.domain_name, domain_dns_value=self.domain_dns_value
            )
            self.assertFalse(mock_requests_post.called)
